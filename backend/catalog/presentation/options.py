from django.db.models import QuerySet

from catalog.models import Program, Sphere
from catalog.presentation.catalog import catalog_order
from catalog.presentation.landing.groups import group_by_sphere
from catalog.schemas import ProgramOptionOut

OTHER_PROGRAMS = "Другие программы"


def option(program: Program, sphere: str) -> ProgramOptionOut:
    return ProgramOptionOut(id=program.hse_id, title=program.title, url=f"/{program.path}", sphere=sphere)


def application_options(programs: QuerySet[Program]) -> list[ProgramOptionOut]:
    grouped = group_by_sphere(list(catalog_order(programs).select_related("sphere")), list(Sphere.objects.all()))
    options = [option(program, group.sphere.title) for group in grouped.spheres for program in group.programs]
    return options + [option(program, OTHER_PROGRAMS) for program in grouped.unassigned]
