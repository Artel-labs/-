import calendar
import math
from dataclasses import dataclass, field
from datetime import date

from catalog.models import Program
from catalog.presentation.cards import kind
from catalog.presentation.dates import day_and_month, epoch_day, format_start, is_upcoming, month_title
from catalog.presentation.facets import short_format
from catalog.presentation.labels import price_label
from catalog.presentation.text import en_dash
from catalog.schemas import MonthOut, StartOut, StartsOut, TickOut

DAY_PX = 32
CARD_WIDTH = 180
GAP_PX = 12
PIN_PAD = 6
PIN_EDGE = 14
DEFAULT_PIN_OFFSET = 28
CHIP_SCROLL_PAD = 8
DAYS_IN_WEEK = 7
PIN_OFFSETS = (CARD_WIDTH - 28, 136, 116, 90, 64, 44, 28)
LANES = ("up1", "down1", "up2", "down2")
NEAR_LANE = {"up2": "up1", "down2": "down1"}
FAR_LANE = {"up1": "up2", "down1": "down2"}
META_SEPARATOR = " · "


@dataclass(frozen=True)
class Placed:
    left: int
    right: int
    x: int


@dataclass
class Board:
    axis_start: int
    width: int
    lanes: dict[str, list[Placed]] = field(default_factory=lambda: {lane: [] for lane in LANES})

    def x_of(self, day_number: int) -> int:
        return (day_number - self.axis_start) * DAY_PX + DAY_PX // 2

    def last_right(self, lane: str) -> float:
        placed = self.lanes[lane]
        return placed[-1].right if placed else -math.inf

    def pin_hits(self, x: int, lane: str) -> bool:
        return any(card.left - PIN_PAD <= x <= card.right + PIN_PAD for card in self.lanes[lane])

    def span_hits_pins(self, left: int, right: int, lane: str) -> bool:
        return any(left - PIN_PAD <= card.x <= right + PIN_PAD for card in self.lanes[lane])

    def fits(self, lane: str, left: int, x: int) -> bool:
        if left < self.last_right(lane) + GAP_PX:
            return False
        if lane in NEAR_LANE:
            return not self.pin_hits(x, NEAR_LANE[lane])
        return not self.span_hits_pins(left, left + CARD_WIDTH, FAR_LANE[lane])

    def clamp(self, left: int) -> int:
        return max(0, min(left, self.width - CARD_WIDTH))

    def free_spot(self, x: int) -> tuple[str, int] | None:
        for lane in LANES:
            for offset in PIN_OFFSETS:
                left = self.clamp(x - offset)
                if PIN_EDGE <= x - left <= CARD_WIDTH - PIN_EDGE and self.fits(lane, left, x):
                    return lane, left
        return None

    def place(self, x: int) -> tuple[str, int]:
        spot = self.free_spot(x) or (min(LANES, key=self.last_right), self.clamp(x - DEFAULT_PIN_OFFSET))
        lane, left = spot
        self.lanes[lane].append(Placed(left, left + CARD_WIDTH, x))
        return lane, left


@dataclass(frozen=True)
class Dated:
    program: Program
    start: date


def upcoming(programs: list[Program], today: date) -> list[Dated]:
    found = [
        Dated(program, program.start_date)
        for program in programs
        if program.start_date and is_upcoming(program.start_date, program.start_month_only, today)
    ]
    return sorted(found, key=lambda item: (item.start, not item.program.start_month_only))


def month_span(first: date, last: date) -> list[tuple[int, int]]:
    months = []
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def last_day(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def when(item: Dated) -> tuple[str, str]:
    if item.program.start_month_only:
        label = month_title(item.start.month)
        return label, label
    return day_and_month(item.start), format_start(item.start, month_only=False)


def start_item(board: Board, item: Dated) -> StartOut:
    program = item.program
    x = board.x_of(epoch_day(item.start))
    lane, left = board.place(x)
    short, full = when(item)
    title = en_dash(program.title)
    return StartOut(
        lane=lane,
        left=left,
        pin=x - left,
        path=program.path,
        hint=f"{title} – старт: {en_dash(full)}",
        when=en_dash(short),
        title=title,
        sphere=program.sphere.slug if program.sphere else "",
        meta=en_dash(META_SEPARATOR.join(part for part in (kind(program), short_format(program.study_format)) if part)),
        price=price_label(program),
    )


def month_out(board: Board, year: int, month: int, items: list[Dated]) -> MonthOut:
    first = epoch_day(date(year, month, 1))
    left = (first - board.axis_start) * DAY_PX
    count = sum(1 for item in items if (item.start.year, item.start.month) == (year, month))
    return MonthOut(
        label=month_title(month),
        count=count,
        left=left,
        width=calendar.monthrange(year, month)[1] * DAY_PX,
        scroll=max(0, left - CHIP_SCROLL_PAD),
    )


def tick_kind(day: date) -> str:
    if day.day == 1:
        return "is-month"
    return "is-week" if day.day % DAYS_IN_WEEK == 0 else ""


def ticks(board: Board, first: date, total_days: int) -> list[TickOut]:
    days = (date.fromordinal(first.toordinal() + offset) for offset in range(total_days))
    return [TickOut(left=board.x_of(epoch_day(day)), kind=tick_kind(day)) for day in days]


def starts_board(programs: list[Program], today: date) -> StartsOut | None:
    items = upcoming(programs, today)
    if not items:
        return None
    first_start, last_start = items[0].start, items[-1].start
    axis_first = first_start.replace(day=1)
    axis_last = last_day(last_start.year, last_start.month)
    total_days = (axis_last - axis_first).days + 1
    board = Board(axis_start=epoch_day(axis_first), width=total_days * DAY_PX)
    starts = [start_item(board, item) for item in items]
    today_number = epoch_day(today)
    return StartsOut(
        width=board.width,
        months=[month_out(board, year, month, items) for year, month in month_span(first_start, last_start)],
        ticks=ticks(board, axis_first, total_days),
        today=board.x_of(today_number) if board.axis_start <= today_number <= epoch_day(axis_last) else None,
        items=starts,
    )
