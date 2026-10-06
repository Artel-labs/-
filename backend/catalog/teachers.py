from catalog.typography import squeeze_spaces

CANONICAL_TEACHER_NAMES = {
    "Дмитрий Максимов": "Максимов Дмитрий Михайлович",
    "Руслан Будник": "Будник Руслан Александрович",
}


def canonical_name(name: str) -> str:
    key = " ".join(name.split())
    return CANONICAL_TEACHER_NAMES.get(key, key)


def shown_name(name: str) -> str:
    return canonical_name(squeeze_spaces(name))
