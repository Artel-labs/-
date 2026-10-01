from catalog.landing_schemas import LinkOut, MenuOut, MenuSphereOut
from catalog.models import Program
from catalog.presentation.landing.groups import Grouped, SphereGroup, catalog_url, plural_programs
from catalog.presentation.text import en_dash

PREVIEW_COUNT = 3


def program_link(program: Program) -> LinkOut:
    return LinkOut(href=f"/{program.path}", title=en_dash(program.title))


def menu_sphere(group: SphereGroup) -> MenuSphereOut:
    href = catalog_url(sphere=group.sphere.slug)
    rest = len(group.programs) - PREVIEW_COUNT
    return MenuSphereOut(
        href=href,
        title=en_dash(group.sphere.title),
        count=plural_programs(len(group.programs)),
        programs=[program_link(program) for program in group.programs[:PREVIEW_COUNT]],
        more=LinkOut(href=href, title=f"ещё {plural_programs(rest)}") if rest > 0 else None,
    )


def menu(grouped: Grouped, total: int) -> MenuOut:
    return MenuOut(spheres=[menu_sphere(group) for group in grouped.spheres], total=total)
