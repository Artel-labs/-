from collections.abc import Callable
from dataclasses import dataclass

from django.conf import settings

from analytics.models import Device
from analytics.summary import Row, SessionRow, Summary, duration_text, half_up

RANGES = (7, 30, 90)
DEFAULT_RANGE = 7
FULL = 100
HOUR_LABEL_STEP = 3
DEVICE_NAMES = dict(Device.choices)


@dataclass(frozen=True)
class Bar:
    name: str
    value: str
    percent: int


@dataclass(frozen=True)
class Kpi:
    value: str
    title: str


@dataclass(frozen=True)
class Hour:
    label: str
    title: str
    percent: int


def range_of(raw: str | None) -> int:
    return int(raw) if raw and raw.isdigit() and int(raw) in RANGES else DEFAULT_RANGE


def number_text(value: float) -> str:
    return f"{value:g}"


def bar(name: str, count: float, peak: float) -> Bar:
    return Bar(name=name, value=number_text(half_up(count, 1)), percent=int(half_up(FULL * count / peak)))


def session_row(row: SessionRow) -> dict[str, object]:
    return {**vars(row), "device": DEVICE_NAMES.get(row.device, row.device), "duration": duration_text(row.duration_ms)}


def row_name(row: Row) -> str:
    return row.name


def bars(rows: list[Row], name: Callable[[Row], str] = row_name) -> list[Bar]:
    peak = max((row.count for row in rows), default=0) or 1
    return [bar(name(row), row.count, peak) for row in rows]


def kpis(summary: Summary) -> list[Kpi]:
    return [
        Kpi(str(summary.visitors_today), "Посетители сегодня"),
        Kpi(str(summary.visitors), "Посетители за период"),
        Kpi(str(summary.pageviews), "Просмотры"),
        Kpi(str(summary.pageviews_today), "Просмотры сегодня"),
        Kpi(duration_text(summary.avg_duration_ms) if summary.avg_duration_ms else "–", "Ср. время на сайте"),
        Kpi(number_text(summary.avg_pages), "Ср. страниц / сессия"),
        Kpi(f"{number_text(summary.bounce_rate)}%", "Отказы"),
        Kpi(str(summary.program_clicks), "Клики по программам"),
    ]


def hours(summary: Summary) -> list[Hour]:
    peak = max(summary.hours) or 1
    return [
        Hour(
            label=str(hour) if hour % HOUR_LABEL_STEP == 0 else "",
            title=f"{hour:02d}:00 · {count}",
            percent=int(half_up(FULL * count / peak)),
        )
        for hour, count in enumerate(summary.hours)
    ]


def context(summary: Summary) -> dict[str, object]:
    return {
        "summary": summary,
        "retention_days": settings.ANALYTICS_RETENTION_DAYS,
        "ranges": RANGES,
        "kpis": kpis(summary),
        "top_pages": bars(summary.top_pages),
        "top_programs": bars(summary.top_programs),
        "top_interest": bars(summary.top_interest),
        "top_paths": bars(summary.top_paths),
        "top_referrers": bars(summary.top_referrers),
        "top_filters": bars(summary.top_filters),
        "devices": bars(summary.devices, lambda row: DEVICE_NAMES.get(row.name, row.name)),
        "daily": bars(summary.daily, lambda row: row.name[5:]),
        "scroll_depth": bars([Row(name=row.name, count=row.avg) for row in summary.scroll_depth]),
        "hours": hours(summary),
        "sessions": [session_row(row) for row in summary.recent_sessions],
    }
