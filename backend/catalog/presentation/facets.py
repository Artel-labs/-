import re
from dataclasses import dataclass

WEEKS_PER_MONTH = 4.345
MONTHS_PER_YEAR = 12
SHORT_MONTHS_LIMIT = 1.5
MEDIUM_MONTHS_LIMIT = 3
NUMBER = re.compile(r"[\d.]+")
LEADING_FLOAT = re.compile(r"\d+(?:\.\d*)?|\.\d+")
FORMAT_DETAILS = re.compile(r"\s*\(.*\)\s*$")


@dataclass(frozen=True)
class Facet:
    value: str
    label: str


@dataclass(frozen=True)
class Badge:
    label: str
    tip: str


UNKNOWN_DURATION = Facet("unknown", "Не указана")
SHORT_DURATION = Facet("short", "До 1,5 месяца")
MEDIUM_DURATION = Facet("medium", "1,5–3 месяца")
LONG_DURATION = Facet("long", "Более 3 месяцев")
DURATION_ORDER = ("short", "medium", "long", "unknown")

FORMAT_FACETS = (
    ("гибрид", Facet("hybrid", "Гибридный")),
    ("смешан", Facet("mixed", "Смешанный")),
    ("онлайн", Facet("online", "Онлайн")),
    ("очн", Facet("offline", "Очно")),
)
OTHER_FORMAT_LABEL = "Другое"

FORMAT_TIPS = (
    (("гибрид",), "Занятия проходят очно и параллельно транслируются онлайн — способ участия можно выбирать."),
    (("смешан",), "Часть занятий проходит очно, часть — онлайн."),
    (("онлайн", "асинхрон"), "Занятия в записи: материалы проходят в удобное время, без привязки к расписанию."),
    (("онлайн", "синхрон"), "Занятия идут онлайн в реальном времени, по расписанию, с преподавателем."),
    (("онлайн",), "Занятия проходят онлайн."),
    (("очн",), "Занятия проходят очно, в аудиториях факультета права НИУ ВШЭ в Москве."),
)

DOC_BADGES = {
    "ПК": Badge("ПК", "Повышение квалификации. Итоговый документ — удостоверение о повышении квалификации НИУ ВШЭ."),
    "ПП": Badge(
        "ПП", "Профессиональная переподготовка. Итоговый документ — диплом о профессиональной переподготовке НИУ ВШЭ."
    ),
}
WORDED_BADGES = (
    ("высш", Badge("Диплом о высшем образовании", "Итоговый документ — диплом о высшем образовании.")),
    ("свидетельств", Badge("Свидетельство об обучении", "Итоговый документ — свидетельство об обучении.")),
)


def format_facet(study_format: str) -> Facet:
    lowered = study_format.lower()
    for fragment, facet in FORMAT_FACETS:
        if fragment in lowered:
            return facet
    return Facet("other", study_format or OTHER_FORMAT_LABEL)


def short_format(study_format: str) -> str:
    return FORMAT_DETAILS.sub("", study_format)


def format_tip(study_format: str) -> str:
    lowered = study_format.lower()
    for fragments, tip in FORMAT_TIPS:
        if all(fragment in lowered for fragment in fragments):
            return tip
    return ""


def doc_badge(kind: str) -> Badge | None:
    kind = kind.strip()
    if kind in DOC_BADGES:
        return DOC_BADGES[kind]
    lowered = kind.lower()
    for fragment, badge in WORDED_BADGES:
        if fragment in lowered:
            return badge
    return Badge(kind, "") if kind else None


def leading_float(token: str) -> float | None:
    found = LEADING_FLOAT.match(token)
    return float(found.group()) if found else None


def duration_in_months(duration: str) -> float | None:
    text = duration.lower().replace(",", ".")
    found = NUMBER.search(text)
    number = leading_float(found.group()) if found else None
    if number is None:
        return None
    if "недел" in text:
        return number / WEEKS_PER_MONTH
    if "месяц" in text:
        return number
    if "год" in text or "лет" in text:
        return number * MONTHS_PER_YEAR
    return None


def duration_facet(duration: str) -> Facet:
    months = duration_in_months(duration) if duration else None
    if months is None:
        return UNKNOWN_DURATION
    if months < SHORT_MONTHS_LIMIT:
        return SHORT_DURATION
    return MEDIUM_DURATION if months <= MEDIUM_MONTHS_LIMIT else LONG_DURATION
