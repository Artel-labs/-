import math
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from analytics.models import Device, Event, EventType

MOSCOW = ZoneInfo("Europe/Moscow")
HOURS_IN_DAY = 24
TOP_PAGES = 12
TOP_PROGRAMS = 15
TOP_FILTERS = 10
TOP_REFERRERS = 10
TOP_PATHS = 12
TOP_INTEREST = 12
TOP_SCROLL = 10
RECENT_SESSIONS = 20
SESSION_PROGRAMS = 5
PROGRAM_INTEREST = 5
CLICK_INTEREST = 0.5
MS_IN_MINUTE = 60_000
HIGH_BOUNCE_PERCENT = 60
HOME_PATHS = ("", "/", "/index.html")
HOME = "Главная"
DIRECT = "(прямой заход)"
HSE_PROGRAM_PATH = "/edu/dpo/"
PROGRAM_ICON = "📘"
HTML_SUFFIX = re.compile(r"\.html$", re.IGNORECASE)
STANDALONE = re.compile(r"\(standalone\)", re.IGNORECASE)


@dataclass
class Row:
    name: str
    count: float


@dataclass
class ScrollRow:
    name: str
    avg: int
    max: int


@dataclass
class Session:
    sid: str
    first: datetime
    last: datetime
    device: str
    pages: set[str] = field(default_factory=set)
    paths: list[str] = field(default_factory=list)
    programs: list[str] = field(default_factory=list)
    dwell_ms: int = 0

    def duration_ms(self) -> int:
        return max(self.dwell_ms, int((self.last - self.first).total_seconds() * 1000))


@dataclass
class SessionRow:
    sid: str
    device: str
    pages: int
    duration_ms: int
    path: list[str]
    programs: list[str]


@dataclass
class Summary:
    days: int
    generated_at: datetime
    visitors: int
    visitors_today: int
    pageviews: int
    pageviews_today: int
    avg_duration_ms: int
    avg_pages: float
    bounce_rate: float
    program_clicks: int
    devices: list[Row]
    hours: list[int]
    daily: list[Row]
    top_pages: list[Row]
    top_programs: list[Row]
    top_filters: list[Row]
    top_referrers: list[Row]
    top_paths: list[Row]
    top_interest: list[Row]
    scroll_depth: list[ScrollRow]
    recent_sessions: list[SessionRow]
    insights: list[str]


def half_up(value: float, digits: int = 0) -> float:
    scale = 10.0**digits
    return float(math.floor(value * scale + 0.5)) / scale


def ratio(part: float, whole: int, digits: int = 0) -> float:
    return half_up(part / whole, digits) if whole else 0


def day_key(moment: datetime) -> str:
    return moment.astimezone(MOSCOW).date().isoformat()


def pretty_path(path: str) -> str:
    if path in HOME_PATHS:
        return HOME
    name = STANDALONE.sub("", HTML_SUFFIX.sub("", unquote(path).removeprefix("/"))).strip()
    return name or path


def is_hse_host(hostname: str) -> bool:
    host = hostname.lower()
    return host in ("hse.ru", "www.hse.ru") or host.endswith(".hse.ru")


def is_program_url(url: str) -> bool:
    parts = urlsplit(url)
    host = parts.hostname or "www.hse.ru"
    return is_hse_host(host) and HSE_PROGRAM_PATH in parts.path.lower()


def program_name(event: Event) -> str:
    if event.label:
        return event.label
    if event.title and event.type == EventType.PROGRAM:
        return event.title
    tail = urlsplit(event.target).path.rstrip("/").split("/")[-1]
    return tail or event.target or "программа"


def same(key: str) -> str:
    return key


def top(counter: Mapping[str, float], limit: int, label: Callable[[str], str] = same) -> list[Row]:
    ordered = sorted(counter.items(), key=lambda item: -item[1])[:limit]
    return [Row(name=label(key), count=count) for key, count in ordered]


class Collector:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.pageviews: list[Event] = []
        self.page_counts: Counter[str] = Counter()
        self.program_clicks: Counter[str] = Counter()
        self.filters: Counter[str] = Counter()
        self.referrers: Counter[str] = Counter()
        self.transitions: Counter[str] = Counter()
        self.interest: defaultdict[str, float] = defaultdict(float)
        self.scroll: dict[str, list[int]] = defaultdict(list)
        self.hours = [0] * HOURS_IN_DAY
        self.days: Counter[str] = Counter()

    def session_of(self, event: Event) -> Session:
        moment = event.occurred_at
        session = self.sessions.setdefault(
            event.session, Session(sid=event.session, first=moment, last=moment, device=event.device)
        )
        session.first = min(session.first, event.occurred_at)
        session.last = max(session.last, event.occurred_at)
        session.device = event.device or session.device
        return session

    def pageview(self, event: Event, session: Session) -> None:
        self.pageviews.append(event)
        session.pages.add(event.path)
        if not session.paths or session.paths[-1] != event.path:
            if session.paths:
                self.transitions[f"{pretty_path(session.paths[-1])} → {pretty_path(event.path)}"] += 1
            session.paths.append(event.path)
        self.page_counts[event.path] += 1
        self.interest[event.path] += 1
        self.days[day_key(event.occurred_at)] += 1
        self.hours[event.occurred_at.astimezone(MOSCOW).hour] += 1
        if event.referrer:
            self.referrers[event.referrer] += 1

    def dwell(self, event: Event, session: Session) -> None:
        session.dwell_ms = max(session.dwell_ms, event.duration_ms)
        if event.path:
            self.interest[event.path] += event.duration_ms / MS_IN_MINUTE

    def program(self, event: Event, session: Session) -> None:
        name = program_name(event)
        self.program_clicks[name] += 1
        session.programs.append(name)
        self.interest[f"program:{name}"] += PROGRAM_INTEREST

    def add(self, event: Event) -> None:
        session = self.session_of(event)
        if event.type == EventType.PAGEVIEW:
            self.pageview(event, session)
        if event.type in (EventType.HEARTBEAT, EventType.EXIT):
            self.dwell(event, session)
        if event.type == EventType.SCROLL and event.path:
            self.scroll[event.path].append(event.scroll)
        if event.type == EventType.PROGRAM or (event.type == EventType.OUTBOUND and is_program_url(event.target)):
            self.program(event, session)
        if event.type == EventType.FILTER and event.label:
            self.filters[event.label] += 1
        if event.type == EventType.CLICK and event.target:
            self.interest[event.path or "click"] += CLICK_INTEREST


def interest_label(key: str) -> str:
    return f"{PROGRAM_ICON} {key.removeprefix('program:')}" if key.startswith("program:") else pretty_path(key)


def scroll_row(path: str, values: list[int]) -> ScrollRow:
    return ScrollRow(name=pretty_path(path), avg=int(half_up(sum(values) / len(values))), max=max(values))


def scroll_depth(scroll: dict[str, list[int]]) -> list[ScrollRow]:
    rows = [scroll_row(path, values) for path, values in scroll.items()]
    return sorted(rows, key=lambda row: -row.avg)[:TOP_SCROLL]


def recent(sessions: list[Session]) -> list[SessionRow]:
    ordered = sorted(sessions, key=lambda session: session.last, reverse=True)[:RECENT_SESSIONS]
    return [
        SessionRow(
            sid=session.sid[:8],
            device=session.device,
            pages=len(session.pages),
            duration_ms=session.duration_ms(),
            path=[pretty_path(path) for path in session.paths],
            programs=session.programs[:SESSION_PROGRAMS],
        )
        for session in ordered
    ]


def daily(days: Counter[str], now: datetime, range_days: int) -> list[Row]:
    keys = [day_key(now - timedelta(days=offset)) for offset in range(range_days - 1, -1, -1)]
    return [Row(name=key, count=days.get(key, 0)) for key in keys]


def duration_text(ms: int) -> str:
    seconds = int(half_up(ms / 1000))
    return f"{seconds} с" if seconds < 60 else f"{half_up(seconds / 60):g} мин"


def insights(summary: Summary) -> list[str]:
    lines = []
    if summary.top_programs:
        best = summary.top_programs[0]
        lines.append(f"Самая интересная программа: «{best.name}» ({best.count:g} кликов).")
    if summary.top_pages:
        page = summary.top_pages[0]
        lines.append(f"Самая посещаемая страница: «{page.name}» ({page.count:g} просмотров).")
    if summary.bounce_rate >= HIGH_BOUNCE_PERCENT:
        lines.append(f"Высокий показатель отказов {summary.bounce_rate:g}% — проверьте первый экран и навигацию.")
    elif summary.visitors:
        lines.append(f"Отказы {summary.bounce_rate:g}% — в пределах нормы для витрины ДПО.")
    if summary.avg_duration_ms > 0:
        lines.append(f"Среднее время на сайте: {duration_text(summary.avg_duration_ms)}.")
    if max(summary.hours) > 0:
        peak = summary.hours.index(max(summary.hours))
        lines.append(f"Пик активности: {peak:02d}:00–{peak:02d}:59.")
    if summary.visitors:
        mobile = next((row.count for row in summary.devices if row.name == Device.MOBILE), 0)
        lines.append(f"С мобильных: {ratio(100 * mobile, summary.visitors):g}% посетителей.")
    else:
        lines.append("Пока нет данных. События появятся, когда посетители примут cookies.")
    return lines


def device_rows(sessions: list[Session]) -> list[Row]:
    counts = Counter(session.device for session in sessions)
    return [Row(name=device, count=counts.get(device, 0)) for device in Device.values]


def build_summary(events: list[Event], now: datetime, range_days: int) -> Summary:
    collector = Collector()
    for event in events:
        collector.add(event)
    sessions = list(collector.sessions.values())
    visitors = len(sessions)
    today = day_key(now)
    summary = Summary(
        days=range_days,
        generated_at=now,
        visitors=visitors,
        visitors_today=sum(1 for session in sessions if day_key(session.first) == today),
        pageviews=len(collector.pageviews),
        pageviews_today=sum(1 for event in collector.pageviews if day_key(event.occurred_at) == today),
        avg_duration_ms=int(ratio(sum(session.duration_ms() for session in sessions), visitors)),
        avg_pages=ratio(sum(len(session.pages) for session in sessions), visitors, 1),
        bounce_rate=ratio(100 * sum(1 for session in sessions if len(session.pages) <= 1), visitors, 1),
        program_clicks=sum(collector.program_clicks.values()),
        devices=device_rows(sessions),
        hours=collector.hours,
        daily=daily(collector.days, now, range_days),
        top_pages=top(collector.page_counts, TOP_PAGES, pretty_path),
        top_programs=top(collector.program_clicks, TOP_PROGRAMS),
        top_filters=top(collector.filters, TOP_FILTERS),
        top_referrers=top(collector.referrers, TOP_REFERRERS, lambda key: key or DIRECT),
        top_paths=top(collector.transitions, TOP_PATHS),
        top_interest=top(collector.interest, TOP_INTEREST, interest_label),
        scroll_depth=scroll_depth(collector.scroll),
        recent_sessions=recent(sessions),
        insights=[],
    )
    summary.insights = insights(summary)
    return summary


def summary_for(range_days: int, now: datetime) -> Summary:
    events = list(Event.objects.filter(occurred_at__gte=now - timedelta(days=range_days)).order_by("pk"))
    return build_summary(events, now, range_days)
