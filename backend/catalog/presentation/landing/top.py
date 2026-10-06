from datetime import date

from catalog.landing_schemas import TopProgramOut
from catalog.models import TOP_PLACES, Program
from catalog.presentation import images
from catalog.presentation.dates import is_upcoming, start_label
from catalog.presentation.facets import doc_badge, format_tip, short_format
from catalog.presentation.landing.collation import SortKey, sort_key

KIND_LABELS = {"ПК": "Повышение квалификации", "ПП": "Переподготовка"}
DEFAULT_KIND = "Программа ДПО"


def kind_label(program: Program) -> str:
    kind = program.type_short or program.type_title
    return KIND_LABELS.get(kind) or kind or DEFAULT_KIND


def upcoming_key(program: Program, today: date) -> date:
    upcoming = program.start_date and is_upcoming(program.start_date, program.start_month_only, today)
    return program.start_date if upcoming and program.start_date else date.max


def by_start(program: Program, today: date) -> tuple[date, SortKey]:
    return upcoming_key(program, today), sort_key(program.title)


def picked(programs: list[Program], today: date) -> list[Program]:
    pinned = sorted(
        (program for program in programs if program.top_position),
        key=lambda program: (program.top_position, *by_start(program, today)),
    )
    rest = sorted(
        (program for program in programs if not program.top_position), key=lambda program: by_start(program, today)
    )
    return (pinned + rest)[:TOP_PLACES]


def tile(program: Program, today: date) -> TopProgramOut:
    thumb = images.thumb(program)
    badge = doc_badge(program.type_short or program.type_title)
    return TopProgramOut(
        image=thumb.src if thumb else "",
        image_webp=thumb.webp if thumb else "",
        id=program.hse_id,
        start=start_label(program.start_date, program.start_month_only, today),
        title=program.title,
        kind=kind_label(program),
        format=short_format(program.study_format),
        format_tip=format_tip(program.study_format),
        doc=badge.label if badge else "",
        doc_tip=badge.tip if badge else "",
        duration=program.duration,
        path=f"/{program.path}",
    )


def top_programs(programs: list[Program], today: date) -> list[TopProgramOut]:
    return [tile(program, today) for program in picked(programs, today)]
