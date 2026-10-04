import re
from typing import Any

PLAIN_CHARS = str.maketrans({" ": " ", " ": "", "—": "-", "–": "-", "«": '"', "»": '"', "„": '"', "“": '"'})
AROUND_DASH = re.compile(r" *- *")
BEFORE_PERCENT = re.compile(r" +%")
BETWEEN_INITIALS = re.compile(r"(?<=\b\w\.) (?=\w\.)")


def untypeset(value: Any) -> Any:
    if isinstance(value, str):
        text = value.translate(PLAIN_CHARS)
        return BETWEEN_INITIALS.sub("", BEFORE_PERCENT.sub("%", AROUND_DASH.sub("-", text)))
    if isinstance(value, dict):
        return {key: untypeset(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [untypeset(item) for item in value]
    return value
