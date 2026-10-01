from datetime import date

from django.conf import settings
from django.db.models import QuerySet

from catalog.branches import BRANCHES
from catalog.landing_schemas import LandingOut
from catalog.models import Program, Sphere
from catalog.presentation.catalog import SHARE_IMAGE_PATH, catalog_order
from catalog.presentation.landing.formats import formats
from catalog.presentation.landing.groups import group_by_sphere
from catalog.presentation.landing.menu import menu
from catalog.presentation.landing.sphere_cards import sphere_cards
from catalog.presentation.landing.strips import reviews, starts
from catalog.presentation.landing.teachers import teachers
from catalog.presentation.landing.top import top_programs


def landing_page(programs: QuerySet[Program], today: date) -> LandingOut:
    ordered = list(
        catalog_order(programs).select_related("sphere").prefetch_related("reviews", "program_teachers__teacher")
    )
    grouped = group_by_sphere(ordered, list(Sphere.objects.all()))
    return LandingOut(
        canonical_url=f"{settings.SITE_URL}/",
        branches=[branch.title for branch in BRANCHES],
        image_url=f"{settings.SITE_URL}{SHARE_IMAGE_PATH}",
        menu=menu(grouped, len(ordered)),
        spheres=sphere_cards(grouped, today),
        formats=formats(ordered, today),
        teachers=teachers(ordered),
        starts=starts(ordered, today),
        reviews=reviews(ordered),
        top=top_programs(ordered, today),
    )
