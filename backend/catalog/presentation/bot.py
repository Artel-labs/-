from datetime import date

from django.db.models import QuerySet

from catalog.models import Program, Sphere
from catalog.presentation.cards import kind, module_titles
from catalog.presentation.catalog import catalog_order
from catalog.presentation.dates import start_label
from catalog.presentation.facets import format_facet
from catalog.presentation.labels import effective_price, price_label
from catalog.presentation.landing.groups import group_by_sphere
from catalog.presentation.options import OTHER_PROGRAMS
from catalog.presentation.text import plain_lines
from catalog.schemas import BotProgramOut
from catalog.typography import squeeze_spaces


def keywords(program: Program) -> list[str]:
    phrases = [*module_titles(program), *plain_lines(program.audience), program.tagline]
    return [squeeze_spaces(phrase) for phrase in phrases if squeeze_spaces(phrase)]


def optional(text: str) -> str | None:
    return squeeze_spaces(text) or None


def bot_program(program: Program, sphere: str, today: date) -> BotProgramOut:
    start = start_label(program.start_date, program.start_month_only, today)
    facet = format_facet(program.study_format)
    return BotProgramOut(
        id=program.hse_id,
        title=squeeze_spaces(program.title),
        url=f"/{program.path}",
        sphere=sphere,
        type=kind(program),
        format=facet.value,
        format_label=squeeze_spaces(program.study_format) or facet.label,
        price=effective_price(program),
        price_label=price_label(program),
        duration=optional(program.duration),
        hours=optional(program.hours),
        schedule=optional(program.schedule),
        start=start or None,
        start_iso=program.start_date.isoformat() if start and program.start_date else None,
        keywords=keywords(program),
    )


def bot_catalog(programs: QuerySet[Program], today: date) -> list[BotProgramOut]:
    ordered = list(catalog_order(programs).select_related("sphere").prefetch_related("modules"))
    grouped = group_by_sphere(ordered, list(Sphere.objects.all()))
    sphere_of = {program.pk: group.sphere.title for group in grouped.spheres for program in group.programs}
    return [bot_program(program, sphere_of.get(program.pk, OTHER_PROGRAMS), today) for program in ordered]
