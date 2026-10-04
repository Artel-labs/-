import json
import re
from typing import Any

from catalog.models import Program, Sphere
from catalog.presentation.dates import format_start
from catalog.presentation.labels import (
    CREDENTIALS,
    DEFAULT_KIND_FOR_DESCRIPTION,
    DOCUMENT_SHORT,
    KIND_FOR_DESCRIPTION,
    effective_price,
    price_label,
)

TITLE_SUFFIX = " · ДПО НИУ ВШЭ"
TITLE_LIMIT = 64
TITLE_BUDGET = TITLE_LIMIT - len(TITLE_SUFFIX)
MIN_TITLE_CUT = 12
MIN_SHORT_TITLE_WORDS = 3
DESCRIPTION_LIMIT = 158
DESCRIPTION_MIN_CUT = 100
ADJECTIVE_MIN_LENGTH = 4
TITLE_OVERRIDES = {
    "1129129055": "Налоговое администрирование и оптимизация",
    "1163275658": "GR в фарме: работа с органами власти",
    "820703080": "Анализ юридических документов",
    "1129129056": "Цифровые инструменты в кадровой работе",
}
TITLE_ADJECTIVE_ENDING = re.compile(r"(ого|его|ых|их|ый|ий|ой|ая|яя|ое|ее|ые|ому|ему|ыми|ими|ую|юю|ов|ев)$", re.I)
TITLE_STOP_WORDS = frozenset(
    [
        "и",
        "а",
        "но",
        "или",
        "в",
        "во",
        "на",
        "с",
        "со",
        "к",
        "ко",
        "по",
        "о",
        "об",
        "от",
        "для",
        "при",
        "из",
        "у",
        "за",
        "до",
        "под",
        "над",
        "про",
        "без",
        "через",
    ]
)
TITLE_BREAK = re.compile(r"\s*[:/(]")
TRAILING_PUNCTUATION = re.compile(r"[\s,;:./—–-]+$")
DESCRIPTION_TAIL = re.compile(r"[\s,.—–-]+$")
COURSE_MODES = {
    "Онлайн": "online",
    "Онлайн синхронный": "online",
    "Онлайн асинхронный": "online",
    "Очный": "onsite",
    "Смешанный": "blended",
    "Гибридный": "blended",
}
PROVIDER = {"@type": "CollegeOrUniversity", "name": "НИУ ВШЭ, факультет права", "sameAs": "https://pravo.hse.ru/"}


def bare(word: str) -> str:
    return re.sub(r"[^а-яёa-z]", "", word.lower())


def is_weak_tail(word: str) -> bool:
    plain = bare(word)
    return plain in TITLE_STOP_WORDS or (
        bool(TITLE_ADJECTIVE_ENDING.search(plain)) and len(plain) > ADJECTIVE_MIN_LENGTH
    )


def title_core(program: Program) -> str:
    if program.hse_id in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[program.hse_id]
    full = program.title.strip()
    cut = TITLE_BREAK.split(full)[0].strip()
    if len(cut) < MIN_TITLE_CUT:
        cut = full
    if len(cut) <= TITLE_BUDGET:
        return cut
    kept: list[str] = []
    for word in cut.split():
        if kept and len(" ".join([*kept, word])) > TITLE_BUDGET:
            break
        kept.append(word)
    while len(kept) > 1 and is_weak_tail(kept[-1]):
        kept.pop()
    return TRAILING_PUNCTUATION.sub("", " ".join(kept)) if len(kept) >= MIN_SHORT_TITLE_WORDS else cut


def page_title(program: Program) -> str:
    return f"{title_core(program)}{TITLE_SUFFIX}"


def meta_description(program: Program) -> str:
    kind = KIND_FOR_DESCRIPTION.get(program.type_short, DEFAULT_KIND_FOR_DESCRIPTION)
    tail = [program.study_format] if program.study_format else []
    start = format_start(program.start_date, program.start_month_only)
    if start:
        tail.append(f"старт {start}")
    price = effective_price(program)
    if price:
        tail.append(price_label(program))
    text = f"{program.title} — {kind} в НИУ ВШЭ."
    if tail:
        text += f" {', '.join(tail)}."
    if program.type_short in DOCUMENT_SHORT:
        text += f" {DOCUMENT_SHORT[program.type_short]}."
    if len(text) <= DESCRIPTION_LIMIT:
        return text
    clipped = text[:DESCRIPTION_LIMIT]
    last_space = clipped.rfind(" ")
    return DESCRIPTION_TAIL.sub("", clipped[:last_space] if last_space > DESCRIPTION_MIN_CUT else clipped) + "…"


def course_instance(program: Program) -> dict[str, str]:
    instance = {"@type": "CourseInstance"}
    mode = COURSE_MODES.get(program.study_format.strip())
    if mode:
        instance["courseMode"] = mode
    if program.start_date:
        instance["startDate"] = program.start_date.isoformat()
    return instance


def course(program: Program, url: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": program.title,
        "description": meta_description(program),
        "url": url,
        "inLanguage": "ru",
        "provider": PROVIDER,
    }
    if program.hse_url:
        data["sameAs"] = program.hse_url
    if program.type_short in CREDENTIALS:
        data["educationalCredentialAwarded"] = CREDENTIALS[program.type_short].name
    instance = course_instance(program)
    if len(instance) > 1:
        data["hasCourseInstance"] = instance
    price = effective_price(program)
    if price is not None:
        category = "Free" if price == 0 else "Paid"
        data["offers"] = {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": "RUB",
            "category": category,
            "url": url,
        }
    return data


def breadcrumbs(program: Program, sphere: Sphere | None, site_url: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = [
        {"@type": "ListItem", "position": 1, "name": "Каталог программ", "item": f"{site_url}/catalog"}
    ]
    if sphere:
        items.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": sphere.title,
                "item": f"{site_url}/catalog?sphere={sphere.slug}",
            }
        )
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": program.title})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def as_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def structured_data(program: Program, site_url: str) -> list[str]:
    url = f"{site_url}/{program.path}"
    return [as_json(course(program, url)), as_json(breadcrumbs(program, program.sphere, site_url))]
