from dataclasses import dataclass

from django.db.models import QuerySet

from catalog.models import Program
from catalog.presentation.catalog import catalog_order
from catalog.schemas import SitemapEntryOut
from core.site import absolute_url


@dataclass(frozen=True)
class Page:
    path: str
    changefreq: str
    priority: str


PAGES = (
    Page("/", "monthly", "1.0"),
    Page("/catalog", "weekly", "0.9"),
    Page("/privacy", "yearly", "0.2"),
    Page("/ratings", "yearly", "0.4"),
)
PROGRAM_CHANGEFREQ = "weekly"
PROGRAM_PRIORITY = "0.7"


def entry(page: Page) -> SitemapEntryOut:
    return SitemapEntryOut(loc=absolute_url(page.path), changefreq=page.changefreq, priority=page.priority)


def program_page(program: Program) -> Page:
    return Page(f"/{program.path}", PROGRAM_CHANGEFREQ, PROGRAM_PRIORITY)


def sitemap(programs: QuerySet[Program]) -> list[SitemapEntryOut]:
    pages = [*PAGES, *(program_page(program) for program in catalog_order(programs))]
    return [entry(page) for page in pages]
