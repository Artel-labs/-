import re
from dataclasses import dataclass
from datetime import date

from catalog.hse.client import is_hse_url
from catalog.landing_schemas import FormatCtaOut, FormatDocOut, FormatOut, FormatStatOut
from catalog.models import Program
from catalog.presentation.landing.groups import catalog_url, nearest_start, plural_programs

DURATION = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s+(\S+)\s*$")
DAYS_IN_UNIT = (("недел", 7), ("месяц", 30), ("дн", 1), ("день", 1))
STUDY_WORDS = ("онлайн", "очно", "смешанно")
APPLY_CTA = FormatCtaOut(href="#contacts", label="Подать заявку", external=False, application=True)


@dataclass(frozen=True)
class Format:
    kind: str | None
    title: str
    desc: str
    document: str
    url: str = ""
    cta_label: str = ""


@dataclass(frozen=True)
class DurationPart:
    number: str
    unit: str
    days: float


FORMATS = (
    Format(
        "ПК",
        "Повышение квалификации",
        "Короткие и ёмкие курсы для практикующих юристов, которые хотят освоить новые компетенции в рамках своей "
        "профессии. Идеальный вариант, чтобы быстро закрыть пробел в знаниях или освоить новую отрасль права.",
        "Итоговый документ: удостоверение о повышении квалификации",
    ),
    Format(
        "ПП",
        "Профессиональная переподготовка",
        "Более длительные и глубокие программы для юристов, которые решили сменить профессиональную траекторию. "
        "Вы получаете системные знания, достаточные для ведения деятельности в новой сфере.",
        "Итоговый документ: диплом о профессиональной переподготовке",
    ),
    Format(
        None,
        "Дополнительное образование для взрослых",
        "Отдельные курсы и модули для слушателей без юридического образования, которые хотят повысить свои знания "
        "в области юриспруденции без привязки к формальной квалификации. Удобный формат для точечного восполнения "
        "пробелов и систематизации знаний в конкретной правовой сфере.",
        "Итоговый документ: свидетельство об обучении (при успешном освоении программы)",
    ),
    Format(
        None,
        "Второе высшее образование",
        "Фундаментальная программа бакалавриата «Юриспруденция: правовое регулирование бизнеса» для тех, у кого нет "
        "юридического образования, но есть потребность получить полноценную юридическую квалификацию. Выбор профиля: "
        "корпоративный юрист или специалист в сфере строительства, недвижимости, финансового и налогового права.",
        "Итоговый документ: диплом о высшем образовании",
        url="https://pravo.hse.ru/doplaw/",
        cta_label="О программе на pravo.hse.ru",
    ),
)
FORMAT_DOCS = {
    "Повышение квалификации": FormatDocOut(
        file="document-pk", ext="png", height=848, name="Удостоверение о повышении квалификации"
    ),
    "Профессиональная переподготовка": FormatDocOut(
        file="document-pp", ext="png", height=848, name="Диплом о профессиональной переподготовке"
    ),
    "Дополнительное образование для взрослых": FormatDocOut(
        file="document-cert", ext="jpg", height=848, name="Свидетельство об обучении"
    ),
    "Второе высшее образование": FormatDocOut(
        file="document-vo", ext="jpg", height=847, name="Диплом о высшем образовании"
    ),
}


def duration_part(raw: str) -> DurationPart | None:
    found = DURATION.match(raw)
    if not found:
        return None
    number, unit = found.groups()
    lowered = unit.lower()
    in_days = next((days for fragment, days in DAYS_IN_UNIT if fragment in lowered), 0)
    return DurationPart(number, unit, float(number.replace(",", ".")) * in_days) if in_days else None


def duration_range(shortest: DurationPart, longest: DurationPart) -> str:
    if shortest.days == longest.days:
        return f"{longest.number} {longest.unit}"
    if shortest.unit == longest.unit:
        return f"{shortest.number} – {longest.number} {longest.unit}"
    return f"{shortest.number} {shortest.unit} – {longest.number} {longest.unit}"


def duration_label(programs: list[Program]) -> str:
    parts = [part for part in (duration_part(program.duration) for program in programs) if part]
    if not parts:
        return ""
    ordered = sorted(parts, key=lambda part: part.days)
    prefix = "обычно " if len(parts) < len(programs) else ""
    return prefix + duration_range(ordered[0], ordered[-1])


def study_word(study_format: str) -> str:
    lowered = study_format.lower()
    if "гибрид" in lowered or "смешан" in lowered:
        return "смешанно"
    if "онлайн" in lowered:
        return "онлайн"
    return "очно" if "очн" in lowered else ""


def study_label(programs: list[Program]) -> str:
    found = {study_word(program.study_format) for program in programs}
    words = [word for word in STUDY_WORDS if word in found]
    if len(words) < 2:
        return "".join(words)
    return f"{', '.join(words[:-1])} и {words[-1]}"


def kind_programs(programs: list[Program], kind: str | None) -> list[Program]:
    return [program for program in programs if kind and (program.type_short or program.type_title) == kind]


def cta(item: Format) -> FormatCtaOut:
    if item.kind:
        return FormatCtaOut(
            href=catalog_url(type=item.kind), label="Смотреть программы", external=False, application=False
        )
    if item.url and is_hse_url(item.url):
        return FormatCtaOut(href=item.url, label=item.cta_label or "Подробнее", external=True, application=False)
    return APPLY_CTA


def stats(programs: list[Program]) -> list[FormatStatOut]:
    rows = (("Длительность", duration_label(programs)), ("Занятия", study_label(programs)))
    return [FormatStatOut(key=key, value=value) for key, value in rows if value]


def format_row(item: Format, programs: list[Program], step: int, today: date) -> FormatOut:
    start = nearest_start(programs, today)
    return FormatOut(
        step=step,
        index=f"{step:02d}",
        title=item.title,
        desc=item.desc,
        document=item.document,
        doc=FORMAT_DOCS.get(item.title),
        stats=stats(programs),
        start=f"Ближайший старт — {start}" if start else "",
        count=plural_programs(len(programs)) if programs else "",
        cta=cta(item),
    )


def formats(programs: list[Program], today: date) -> list[FormatOut]:
    shown = [(item, kind_programs(programs, item.kind)) for item in FORMATS]
    visible = [(item, items) for item, items in shown if not (item.kind and not items)]
    return [format_row(item, items, step, today) for step, (item, items) in enumerate(visible, start=1)]
