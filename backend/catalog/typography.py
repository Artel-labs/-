import re
from collections.abc import Callable

NBSP = "\u00a0"
HAIR_SPACE = "\u200a"
EM_DASH = "—"
EN_DASH = "–"
CYRILLIC = "А-Яа-яЁё"
UPPER = "А-ЯЁ"
SHORT_WORD = re.compile(rf"(?<![\w\-])([{CYRILLIC}]{{1,2}}) +(?=\S)")
NUMBER_AND_UNIT = re.compile(rf"(\d) +(?=[\d{CYRILLIC}₽№])")
PERCENT = re.compile(r"(\d) ?%")
COPYRIGHT = re.compile(r"©[ \u00a0]*")
PUNCTUATION_DASH = re.compile(r"(?<=\S)[ \u00a0]+[-–—][ \u00a0]+(?=\S)")
SPACE_BEFORE_DASH = re.compile(r"(?<=\S) +—")
TIME_RANGE = re.compile(r"(\d{1,2}[:.]\d{2}) *[-–—] *(\d{1,2}[:.]\d{2})")
NUMBER_RANGE = re.compile(r"(?<![\d.,:/\-–])(\d{1,4})-(\d{1,4})(?![\d\-])")
STRAIGHT_QUOTES = re.compile(r'"([^"\n]+)"')
INITIALS = re.compile(rf"\b([{UPPER}])\. ?([{UPPER}])\.")
SURNAME_BEFORE = re.compile(rf"([{UPPER}][а-яё]+) +(?=[{UPPER}]\.{HAIR_SPACE}[{UPPER}]\.)")
SURNAME_AFTER = re.compile(rf"([{UPPER}]\.{HAIR_SPACE}[{UPPER}]\.) +(?=[{UPPER}][а-яё])")
REGULAR_SPACES = re.compile(r"[ \t\r\n\f\v]+")


def straight_quotes(text: str) -> str:
    return STRAIGHT_QUOTES.sub(r"«\1»", text)


def nested_quotes(text: str) -> str:
    if text.count("«") != text.count("»"):
        return text
    depth = 0
    result = []
    for char in text:
        if char == "«":
            result.append("„" if depth else char)
            depth += 1
        elif char == "»":
            depth -= 1
            result.append("“" if depth else char)
        else:
            result.append(char)
    return "".join(result)


def ranges(text: str) -> str:
    return NUMBER_RANGE.sub(rf"\1{EN_DASH}\2", TIME_RANGE.sub(rf"\1{EN_DASH}\2", text))


def dashes(text: str) -> str:
    return SPACE_BEFORE_DASH.sub(NBSP + EM_DASH, PUNCTUATION_DASH.sub(f"{NBSP}{EM_DASH} ", text))


def initials(text: str) -> str:
    text = INITIALS.sub(rf"\1.{HAIR_SPACE}\2.", text)
    return SURNAME_AFTER.sub(rf"\1{NBSP}", SURNAME_BEFORE.sub(rf"\1{NBSP}", text))


def no_break_spaces(text: str) -> str:
    text = COPYRIGHT.sub("©" + NBSP, PERCENT.sub(rf"\1{NBSP}%", text))
    return NUMBER_AND_UNIT.sub(rf"\1{NBSP}", SHORT_WORD.sub(rf"\1{NBSP}", text))


RULES: tuple[Callable[[str], str], ...] = (straight_quotes, nested_quotes, ranges, dashes, initials, no_break_spaces)


def typeset(text: str) -> str:
    for rule in RULES:
        text = rule(text)
    return text


def squeeze_spaces(text: str) -> str:
    return REGULAR_SPACES.sub(" ", text).strip()


def plain_spaces(text: str) -> str:
    return " ".join(text.split())
