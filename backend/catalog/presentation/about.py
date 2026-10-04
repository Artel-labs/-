import re
from dataclasses import dataclass

from catalog.models import Program
from catalog.typography import squeeze_spaces

GLUED_MIN_LENGTH = 150
GLUED_MIN_JUNCTIONS = 3
LEAD_PREFIX_LENGTH = 60
SENTENCE_END = re.compile(r"[.!?](\s|$)")
JUNCTION = re.compile(r"[а-яё)»\"%](?=\s+[А-ЯЁ])")
JUNCTION_SPLIT = re.compile(r"(?<=[а-яё)»\"%])\s+(?=[А-ЯЁ])")


@dataclass(frozen=True)
class About:
    lead: str
    body: str
    items: list[str]


def glued_items(text: str) -> list[str]:
    if len(text) < GLUED_MIN_LENGTH or SENTENCE_END.search(text):
        return []
    if len(JUNCTION.findall(text)) < GLUED_MIN_JUNCTIONS:
        return []
    return [part.strip() for part in JUNCTION_SPLIT.split(text) if part.strip()]


def simplified(text: str) -> str:
    return " ".join(text.split()).lower()


def about(program: Program) -> About | None:
    tagline, body = squeeze_spaces(program.tagline), squeeze_spaces(program.about)
    if not tagline and not body:
        return None
    lead_repeats_body = bool(tagline and body and simplified(body).startswith(simplified(tagline)[:LEAD_PREFIX_LENGTH]))
    items = glued_items(body)
    return About(lead="" if lead_repeats_body else tagline, body="" if items else body, items=items)
