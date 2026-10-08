from collections import Counter
from collections.abc import Iterable

from catalog.models import Program, Sphere
from catalog.presentation.cards import OTHER_SPHERE, kind
from catalog.presentation.facets import DURATION_ORDER, Facet, duration_facet, format_facet
from catalog.schemas import ChipOut, FiltersOut

ALL = "all"
ALL_TYPES = "Все программы"
ALL_FORMATS = "Любой формат"
ALL_SPHERES = "Все направления"
ALL_DURATIONS = "Любая длительность"
OTHER_TYPE = "Другое"
OTHER_SPHERE_TITLE = "Прочее"
TYPE_CHIP_LABELS = {"ПК": "ПК · Повышение квалификации", "ПП": "ПП · Профессиональная переподготовка"}


def chip(label: str, value: str, count: int, active: bool = False) -> ChipOut:
    return ChipOut(label=f"{label} ({count})", name=label, count=count, value=value, active=active)


def group(all_label: str, total: int, options: Iterable[tuple[str, str, int]]) -> list[ChipOut]:
    return [chip(all_label, ALL, total, active=True), *(chip(label, value, count) for label, value, count in options)]


def type_options(programs: list[Program]) -> list[tuple[str, str, int]]:
    counts = Counter(kind(program) or OTHER_TYPE for program in programs)
    return [(TYPE_CHIP_LABELS.get(key, key), key, count) for key, count in counts.items()]


def tally(facets: list[Facet]) -> list[tuple[str, str, int]]:
    counts = Counter(facet.value for facet in facets)
    labels = {facet.value: facet.label for facet in facets}
    return [(labels[value], value, count) for value, count in counts.items()]


def format_options(programs: list[Program]) -> list[tuple[str, str, int]]:
    return tally([format_facet(program.study_format) for program in programs])


def sphere_options(programs: list[Program], spheres: list[Sphere]) -> list[tuple[str, str, int]]:
    counts = Counter(program.sphere_id for program in programs)
    options = [(sphere.title, sphere.slug, counts[sphere.pk]) for sphere in spheres if counts[sphere.pk]]
    if counts[None]:
        options.append((OTHER_SPHERE_TITLE, OTHER_SPHERE, counts[None]))
    return options


def duration_options(programs: list[Program]) -> list[tuple[str, str, int]]:
    options = tally([duration_facet(program.duration) for program in programs])
    return sorted(options, key=lambda option: DURATION_ORDER.index(option[1]))


def filters(programs: list[Program], spheres: list[Sphere]) -> FiltersOut:
    total = len(programs)
    return FiltersOut(
        type=group(ALL_TYPES, total, type_options(programs)),
        format=group(ALL_FORMATS, total, format_options(programs)),
        sphere=group(ALL_SPHERES, total, sphere_options(programs, spheres)),
        duration=group(ALL_DURATIONS, total, duration_options(programs)),
    )
