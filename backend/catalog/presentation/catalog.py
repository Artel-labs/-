from datetime import date

from django.conf import settings
from django.db.models import Case, IntegerField, QuerySet, Value, When

from catalog.models import Program, Source, Sphere
from catalog.presentation.cards import card
from catalog.presentation.filters import filters
from catalog.presentation.item_list import item_list
from catalog.presentation.timeline import starts_board
from catalog.schemas import CatalogPageOut
from core.site import SHARE_IMAGE_PATH, absolute_url

HSE_FIRST = 0
MANUAL_LAST = 1
CATALOG_PATH = "/catalog"


def catalog_order(programs: QuerySet[Program]) -> QuerySet[Program]:
    manual_last = Case(
        When(source=Source.MANUAL, then=Value(MANUAL_LAST)), default=Value(HSE_FIRST), output_field=IntegerField()
    )
    return programs.annotate(manual_last=manual_last).order_by("manual_last", "catalog_position", "pk")


def catalog_page(programs: QuerySet[Program], today: date) -> CatalogPageOut:
    ordered = list(catalog_order(programs).select_related("sphere").prefetch_related("modules", "program_teachers"))
    return CatalogPageOut(
        total=len(ordered),
        canonical_url=absolute_url(CATALOG_PATH),
        image_url=absolute_url(SHARE_IMAGE_PATH),
        filters=filters(ordered, list(Sphere.objects.all())),
        cards=[card(program, today) for program in ordered],
        starts=starts_board(ordered, today),
        structured_data=item_list(ordered, settings.SITE_URL),
    )
