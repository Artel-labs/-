from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from catalog.landing_schemas import LandingOut
from catalog.models import Program
from catalog.presentation.bot import bot_catalog
from catalog.presentation.catalog import catalog_page
from catalog.presentation.dates import moscow_today
from catalog.presentation.landing.page import landing_page
from catalog.presentation.options import application_options
from catalog.presentation.page import program_page
from catalog.presentation.sitemap import sitemap
from catalog.presentation.tg import tg_catalog
from catalog.schemas import (
    BotProgramOut,
    CatalogPageOut,
    ProgramOptionOut,
    ProgramPageOut,
    SitemapEntryOut,
    TgCatalogOut,
)

router = Router(tags=["Каталог"])


def published() -> QuerySet[Program]:
    return Program.objects.filter(is_published=True).select_related("sphere")


@router.get("/programs/{hse_id}", response=ProgramPageOut)
def program_detail(request: HttpRequest, hse_id: str) -> ProgramPageOut:
    return program_page(get_object_or_404(published(), hse_id=hse_id), moscow_today())


@router.get("/programs", response=CatalogPageOut)
def program_list(request: HttpRequest) -> CatalogPageOut:
    return catalog_page(published(), moscow_today())


@router.get("/landing", response=LandingOut)
def landing(request: HttpRequest) -> LandingOut:
    return landing_page(published(), moscow_today())


@router.get("/program-options", response=list[ProgramOptionOut])
def program_options(request: HttpRequest) -> list[ProgramOptionOut]:
    return application_options(published())


@router.get("/sitemap", response=list[SitemapEntryOut])
def sitemap_entries(request: HttpRequest) -> list[SitemapEntryOut]:
    return sitemap(published())


@router.get("/bot", response=list[BotProgramOut])
def bot_programs(request: HttpRequest) -> list[BotProgramOut]:
    return bot_catalog(published(), moscow_today())


@router.get("/tg", response=TgCatalogOut)
def telegram_catalog(request: HttpRequest) -> TgCatalogOut:
    return tg_catalog(published(), moscow_today())
