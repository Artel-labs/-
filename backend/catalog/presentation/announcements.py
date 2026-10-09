from datetime import date

from django.db.models import QuerySet

from catalog.models import Program
from catalog.presentation.catalog import catalog_order
from catalog.presentation.timeline import starts_board
from catalog.schemas import AnnouncementsPageOut
from core.site import absolute_url

ANNOUNCEMENTS_PATH = "/announcements"


def announcements_page(programs: QuerySet[Program], today: date) -> AnnouncementsPageOut:
    ordered = list(catalog_order(programs).select_related("sphere"))
    return AnnouncementsPageOut(canonical_url=absolute_url(ANNOUNCEMENTS_PATH), starts=starts_board(ordered, today))
