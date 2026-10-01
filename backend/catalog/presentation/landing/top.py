import re
from datetime import date

from catalog.landing_schemas import TopProgramOut
from catalog.models import Program
from catalog.presentation import images
from catalog.presentation.dates import is_upcoming, start_label
from catalog.presentation.facets import doc_badge, format_tip, short_format
from catalog.presentation.labels import FREE, PRICE_ON_REQUEST, effective_price
from catalog.presentation.landing.collation import sort_key
from catalog.presentation.text import en_dash

TOP_COUNT = 15
CURATED_IDS = ("837181759", "816497962", "474596729", "1008772871", "474599435")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
NO_BREAK_SPACE = " "
KIND_LABELS = {"ПК": "Повышение квалификации", "ПП": "Переподготовка"}
DEFAULT_KIND = "Программа ДПО"


def tile_price(program: Program) -> str:
    price = effective_price(program)
    if price is None:
        return PRICE_ON_REQUEST
    if price == 0:
        return FREE
    return f"{price:,}".replace(",", NO_BREAK_SPACE) + f"{NO_BREAK_SPACE}₽"


def kind_label(program: Program) -> str:
    kind = program.type_short or program.type_title
    return KIND_LABELS.get(kind) or kind or DEFAULT_KIND


def first_sentence(program: Program) -> str:
    source = (program.tagline or program.about).strip()
    return en_dash(SENTENCE_END.split(source)[0]) if source else ""


def upcoming_key(program: Program, today: date) -> date:
    upcoming = program.start_date and is_upcoming(program.start_date, program.start_month_only, today)
    return program.start_date if upcoming and program.start_date else date.max


def picked(programs: list[Program], today: date) -> list[Program]:
    by_id = {program.hse_id: program for program in programs}
    curated = [by_id[hse_id] for hse_id in CURATED_IDS if hse_id in by_id]
    rest = sorted(
        (program for program in programs if program.hse_id not in CURATED_IDS),
        key=lambda program: (upcoming_key(program, today), sort_key(program.title)),
    )
    return (curated + rest)[:TOP_COUNT]


def tile(program: Program, rank: int, today: date) -> TopProgramOut:
    thumb = images.thumb(program)
    badge = doc_badge(program.type_short or program.type_title)
    return TopProgramOut(
        image=thumb.src if thumb else "",
        image_webp=thumb.webp if thumb else "",
        id=program.hse_id,
        start=start_label(program.start_date, program.start_month_only, today),
        rank=str(rank),
        title=en_dash(program.title),
        tagline=first_sentence(program),
        kind=kind_label(program),
        format=short_format(program.study_format),
        format_tip=format_tip(program.study_format),
        doc=badge.label if badge else "",
        doc_tip=badge.tip if badge else "",
        duration=program.duration,
        price=tile_price(program),
        path=f"/{program.path}",
    )


def top_programs(programs: list[Program], today: date) -> list[TopProgramOut]:
    return [tile(program, rank, today) for rank, program in enumerate(picked(programs, today), start=1)]
