from datetime import date

from catalog.landing_schemas import SphereCardOut
from catalog.models import Program
from catalog.presentation.landing.groups import Grouped, SphereGroup, catalog_url, nearest_start, plural_programs

FILTERS_ANCHOR = "#filters"
FACT_SEPARATOR = " · "
SPHERE_LEADS = {
    "corporate": "Договоры по российскому, английскому и гонконгскому праву, корпоративные споры и деловые переговоры",
    "digital": "Интеллектуальная собственность, авторское право, цифровые инструменты в работе и нейроправо",
    "international": "Право Франции, ЕС и Китая, трансграничные операции и морской арбитраж",
    "finance": "Налоговое администрирование, банкротство и исламские финансы",
    "language": "Юридический английский и французский для практикующих юристов",
    "practice": "Бизнес-медиация, GR в фарме, анализ юридических документов и транспортное право",
}
KIND_SHORTS = ("ПК", "ПП")


def kinds_label(programs: list[Program]) -> str:
    counts = {
        kind: sum(1 for program in programs if (program.type_short or program.type_title) == kind)
        for kind in KIND_SHORTS
    }
    return FACT_SEPARATOR.join(f"{count} {kind}" for kind, count in counts.items() if count)


def facts(programs: list[Program], today: date) -> list[str]:
    summary = FACT_SEPARATOR.join(part for part in (plural_programs(len(programs)), kinds_label(programs)) if part)
    nearest = nearest_start(programs, today)
    return [summary, f"Ближайший старт — {nearest}"] if nearest else [summary]


def sphere_card(group: SphereGroup, index: int, today: date) -> SphereCardOut:
    slug = group.sphere.slug
    return SphereCardOut(
        slug=slug,
        href=catalog_url(sphere=slug) + FILTERS_ANCHOR,
        index=f"{index:02d}",
        title=group.sphere.title,
        lead=SPHERE_LEADS.get(slug, ""),
        facts=facts(group.programs, today),
    )


def sphere_cards(grouped: Grouped, today: date) -> list[SphereCardOut]:
    return [sphere_card(group, index, today) for index, group in enumerate(grouped.spheres, start=1)]
