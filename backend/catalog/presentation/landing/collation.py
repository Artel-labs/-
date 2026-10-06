import unicodedata

SPACE, PUNCTUATION, DIGIT, CYRILLIC, LATIN, OTHER = range(6)
SECONDARY_LETTERS = {"ё": "е"}


def char_group(char: str) -> int:
    if char.isspace():
        return SPACE
    if char.isdigit():
        return DIGIT
    if not char.isalpha():
        return PUNCTUATION
    name = unicodedata.name(char, "")
    if name.startswith("CYRILLIC"):
        return CYRILLIC
    return LATIN if name.startswith("LATIN") else OTHER


def primary_key(text: str) -> list[tuple[int, str]]:
    lowered = text.lower()
    return [(char_group(char), SECONDARY_LETTERS.get(char, char)) for char in lowered]


SortKey = tuple[list[tuple[int, str]], str, list[bool]]


def sort_key(text: str) -> SortKey:
    return primary_key(text), text.lower(), [char.isupper() for char in text]
