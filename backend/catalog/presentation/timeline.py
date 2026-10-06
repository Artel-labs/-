from dataclasses import dataclass
from datetime import date
from itertools import groupby

from catalog.models import Program, Sphere
from catalog.presentation.cards import kind
from catalog.presentation.dates import day_and_month, format_start, is_upcoming, month_title
from catalog.presentation.facets import short_format
from catalog.presentation.labels import price_label
from catalog.presentation.text import plural
from catalog.schemas import SphereOut, StartMonthOut, StartOut, StartsOut

SIDES = ("left", "right")
CAPTION_SEPARATOR = " · "
META_SEPARATOR = " · "
ANCHOR_PREFIX = "starts"


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


def when(item: Dated) -> tuple[str, str]:
    if item.program.start_month_only:
        label = month_title(item.start.month)
        return label, label
    return day_and_month(item.start), format_start(item.start, month_only=False)


def start_item(item: Dated, index: int) -> StartOut:
    program = item.program
    short, full = when(item)
    title = program.title
    return StartOut(
        side=SIDES[index % len(SIDES)],
        path=program.path,
        hint=f"{title} — старт: {full}",
        when=short,
        title=title,
        sphere=program.sphere.slug if program.sphere else "",
        meta=META_SEPARATOR.join(part for part in (kind(program), short_format(program.study_format)) if part),
        price=price_label(program),
    )


def month_key(item: Dated) -> tuple[int, int]:
    return item.start.year, item.start.month


def month_out(year: int, month: int, items: list[StartOut]) -> StartMonthOut:
    label = month_title(month)
    return StartMonthOut(
        anchor=f"{ANCHOR_PREFIX}-{year}-{month:02d}",
        label=label,
        caption=f"{label}{CAPTION_SEPARATOR}{plural(len(items), 'старт', 'старта', 'стартов')}",
        items=items,
    )


def legend(items: list[Dated]) -> list[SphereOut]:
    spheres: dict[int, Sphere] = {item.program.sphere.pk: item.program.sphere for item in items if item.program.sphere}
    ordered = sorted(spheres.values(), key=lambda sphere: (sphere.position, sphere.title))
    return [SphereOut(slug=sphere.slug, title=sphere.title) for sphere in ordered]


def starts_board(programs: list[Program], today: date) -> StartsOut | None:
    items = upcoming(programs, today)
    if not items:
        return None
    placed = list(zip(items, (start_item(item, index) for index, item in enumerate(items)), strict=True))
    months = [
        month_out(year, month, [out for _, out in group])
        for (year, month), group in groupby(placed, key=lambda pair: month_key(pair[0]))
    ]
    return StartsOut(months=months, legend=legend(items))
