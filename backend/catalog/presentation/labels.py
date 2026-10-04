from dataclasses import dataclass

from catalog.formatting import format_price
from catalog.models import FileKind, Program

TYPE_LABELS = {"ПК": "Повышение квалификации", "ПП": "Профессиональная переподготовка"}
DEFAULT_TYPE_LABEL = "Программа ДПО"
KIND_FOR_DESCRIPTION = {"ПК": "повышение квалификации", "ПП": "профессиональная переподготовка"}
DEFAULT_KIND_FOR_DESCRIPTION = "программа ДПО"
DOCUMENT_SHORT = {"ПК": "Удостоверение НИУ ВШЭ", "ПП": "Диплом о профессиональной переподготовке НИУ ВШЭ"}
FILE_LABELS: dict[str, str] = {FileKind.PLAN: "Учебный план", FileKind.SCHEDULE: "Расписание занятий"}
PRICE_ON_REQUEST = "Цена по запросу"
FREE = "Бесплатно"
UNKNOWN = "уточняется"


@dataclass(frozen=True)
class Credential:
    tag: str
    name: str
    note: str


CREDENTIALS = {
    "ПК": Credential(
        "ПК", "Удостоверение о повышении квалификации", "Подтверждает новые компетенции в рамках текущей профессии."
    ),
    "ПП": Credential(
        "ПП",
        "Диплом о профессиональной переподготовке",
        "Даёт право вести профессиональную деятельность в новой области.",
    ),
}


def type_label(program: Program) -> str:
    return TYPE_LABELS.get(program.type_short) or program.type_short or DEFAULT_TYPE_LABEL


def effective_price(program: Program) -> int | None:
    return program.price if program.price is not None else program.base_price


def price_label(program: Program) -> str:
    price = effective_price(program)
    if price is None:
        return PRICE_ON_REQUEST
    return FREE if price == 0 else format_price(price)
