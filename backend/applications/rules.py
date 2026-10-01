import re

EMAIL_PART = r"[^\s@,;?#%/\\<>\"&=:]"
EMAIL_SHAPE = re.compile(rf"{EMAIL_PART}+@{EMAIL_PART}+\.{EMAIL_PART}{{2,}}")
PHONE_ALLOWED = re.compile(r"[0-9+()\-\s.]+")
PHONE_MIN_DIGITS = 10
PHONE_MAX_DIGITS = 15
EMAIL_TYPO = "Проверьте адрес почты: похоже, в нём опечатка."
PHONE_BAD_CHARS = "В телефоне допустимы только цифры, пробелы и знаки + ( ) -"
PHONE_BAD_LENGTH = "Проверьте телефон: нужен номер с кодом страны или города."


def email_looks_valid(value: str) -> bool:
    return bool(EMAIL_SHAPE.fullmatch(value))


def phone_problem(value: str) -> str:
    if not PHONE_ALLOWED.fullmatch(value):
        return PHONE_BAD_CHARS
    digits = sum(char.isdigit() for char in value)
    return PHONE_BAD_LENGTH if not PHONE_MIN_DIGITS <= digits <= PHONE_MAX_DIGITS else ""
