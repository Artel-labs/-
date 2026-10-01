from dataclasses import dataclass, field
from datetime import date
from urllib.parse import quote

from catalog.models import Program, Sphere
from catalog.presentation.dates import format_start, is_upcoming
from catalog.presentation.text import plural

CATALOG_PATH = "/catalog"


@dataclass
class SphereGroup:
    sphere: Sphere
    programs: list[Program] = field(default_factory=list)


@dataclass(frozen=True)
class Grouped:
    spheres: list[SphereGroup]
    unassigned: list[Program]


def plural_programs(count: int) -> str:
    return plural(count, "программа", "программы", "программ")


def catalog_url(**params: str) -> str:
    query = "&".join(f"{key}={quote(value, safe='')}" for key, value in params.items())
    return f"{CATALOG_PATH}?{query}" if query else CATALOG_PATH


def group_by_sphere(programs: list[Program], spheres: list[Sphere]) -> Grouped:
    groups = {sphere.pk: SphereGroup(sphere) for sphere in spheres}
    unassigned = []
    for program in programs:
        group = groups.get(program.sphere_id) if program.sphere_id else None
        if group:
            group.programs.append(program)
        else:
            unassigned.append(program)
    for group in groups.values():
        group.programs.sort(key=lambda program: program.position)
    return Grouped([group for group in groups.values() if group.programs], unassigned)


def nearest_start(programs: list[Program], today: date) -> str:
    upcoming = sorted(
        (program for program in programs if is_upcoming(program.start_date, program.start_month_only, today)),
        key=lambda program: program.start_date or date.max,
    )
    return format_start(upcoming[0].start_date, upcoming[0].start_month_only) if upcoming else ""
