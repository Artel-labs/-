import re
from typing import Any

from catalog.models import Program
from catalog.presentation.facets import format_facet
from catalog.presentation.labels import effective_price
from catalog.presentation.seo import PROVIDER, as_json

LIST_NAME = "Программы ДПО факультета права НИУ ВШЭ"
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
PARTIAL_WORD = re.compile(r"\s+\S*$")
MIN_SENTENCE_LENGTH = 40
DESCRIPTION_LIMIT = 300
DESCRIPTION_CUT = 297
ELLIPSIS = "…"
COURSE_MODES = {"online": "online", "offline": "onsite", "mixed": "blended", "hybrid": "blended"}
RETRAINING = "ПП"
RETRAINING_KIND = "Профессиональная переподготовка"
DEFAULT_KIND = "Повышение квалификации"


def course_description(program: Program) -> str:
    source = (program.tagline or program.about).strip()
    if not source:
        kind = RETRAINING_KIND if program.type_short == RETRAINING else DEFAULT_KIND
        return f"{kind}: {program.title}. Факультет права НИУ ВШЭ."
    first_sentence = SENTENCE_END.split(source)[0].strip()
    text = first_sentence if len(first_sentence) >= MIN_SENTENCE_LENGTH else source
    if len(text) > DESCRIPTION_LIMIT:
        text = PARTIAL_WORD.sub("", text[:DESCRIPTION_CUT]) + ELLIPSIS
    return text


def course_instance(program: Program) -> dict[str, str]:
    instance = {"@type": "CourseInstance"}
    mode = COURSE_MODES.get(format_facet(program.study_format).value)
    if mode:
        instance["courseMode"] = mode
    if program.start_date:
        instance["startDate"] = program.start_date.isoformat()
    return instance


def course(program: Program, site_url: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@type": "Course",
        "name": program.title,
        "description": course_description(program),
        "url": f"{site_url}/{program.path}",
        "inLanguage": "ru",
        "provider": PROVIDER,
    }
    if program.hse_url:
        data["sameAs"] = program.hse_url
    instance = course_instance(program)
    if len(instance) > 1:
        data["hasCourseInstance"] = instance
    price = effective_price(program)
    if price:
        data["offers"] = {"@type": "Offer", "price": str(price), "priceCurrency": "RUB", "category": "Paid"}
    return data


def item_list(programs: list[Program], site_url: str) -> str:
    elements = [
        {"@type": "ListItem", "position": position, "item": course(program, site_url)}
        for position, program in enumerate(programs, start=1)
    ]
    return as_json(
        {"@context": "https://schema.org", "@type": "ItemList", "name": LIST_NAME, "itemListElement": elements}
    )
