import re
import unicodedata

MAX_SLUG_LENGTH = 60
FALLBACK_SLUG = "programma"
TRANSLITERATION = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh",
    "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}  # fmt: skip


def transliterate(text: str) -> str:
    return "".join(TRANSLITERATION.get(char, char) for char in text.lower())


def slugify(title: str) -> str:
    plain = unicodedata.normalize("NFD", transliterate(title))
    plain = "".join(char for char in plain if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")[:MAX_SLUG_LENGTH].rstrip("-")
    return slug or FALLBACK_SLUG


def program_path(title: str, hse_id: str) -> str:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", hse_id)
    suffix = f"-{safe_id}" if safe_id else ""
    return f"programs/{slugify(title)}{suffix}.html"
