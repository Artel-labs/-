from dataclasses import dataclass

from catalog.models import Sphere
from catalog.typography import plain_spaces


@dataclass(frozen=True)
class SphereRule:
    slug: str
    title: str
    fragments: tuple[str, ...]


SPHERE_RULES = (
    SphereRule(
        "corporate",
        "Корпоративное и договорное право",
        (
            "Актуальные вопросы гражданского права",
            "Контрактное право Гонконга",
            "Английское контрактное право",
            "Корпоративное право",
            "Деловые переговоры",
            "Общие вопросы договорного права",
            "Искусство составления договоров",
        ),
    ),
    SphereRule(
        "digital",
        "Цифровое право и интеллектуальная собственность",
        (
            "Интеллектуальная собственность",
            "Цифровое право для бизнеса",
            "Авторское право",
            "Безопасное внедрение цифровых инструментов",
            "Нейроправо",
        ),
    ),
    SphereRule(
        "international",
        "Международное и зарубежное право",
        (
            "Французское (европейское) экономическое право",
            "Международное частное право",
            "Введение в правовую систему Китая",
            "Морской арбитраж",
        ),
    ),
    SphereRule(
        "finance",
        "Финансы, налоги и банкротство",
        ("налогового администрирования", "Правовые вопросы банкротства", "Исламские финансы", "Налоговые проверки"),
    ),
    SphereRule(
        "language",
        "Иностранные языки для юристов",
        ("Мастерство юридического английского", "Право на английском", "Французский юридический язык"),
    ),
    SphereRule(
        "practice",
        "Практика, переговоры и отраслевое регулирование",
        (
            "Персональный ассистент",
            "Имущественные отношения в семье",
            "GR в фарме",
            "Бизнес-медиация",
            "Техники эффективного анализа",
            "Транспортное право",
            "Трудовое право для кадровых работников",
            "Юридическая ответственность врача",
            "трансляционной медицины",
            "Market Access",
        ),
    ),
)


@dataclass(frozen=True)
class SphereMatch:
    slug: str
    position: int


def ensure_spheres() -> dict[str, Sphere]:
    spheres = {}
    for position, rule in enumerate(SPHERE_RULES):
        sphere, _ = Sphere.objects.update_or_create(
            slug=rule.slug, defaults={"title": rule.title, "position": position}
        )
        spheres[rule.slug] = sphere
    return spheres


def match_sphere(title: str) -> SphereMatch | None:
    lowered = plain_spaces(title).lower()
    for rule in SPHERE_RULES:
        for position, fragment in enumerate(rule.fragments):
            if fragment.lower() in lowered:
                return SphereMatch(rule.slug, position)
    return None
