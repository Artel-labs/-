from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from catalog.models import Program
from catalog.presentation.catalog import catalog_page
from catalog.presentation.dates import moscow_today
from catalog.presentation.page import program_page
from catalog.schemas import CatalogPageOut, ProgramPageOut

router = Router(tags=["Каталог"])


def published() -> QuerySet[Program]:
    return Program.objects.filter(is_published=True).select_related("sphere")


@router.get("/programs/{hse_id}", response=ProgramPageOut)
def program_detail(request: HttpRequest, hse_id: str) -> ProgramPageOut:
    return program_page(get_object_or_404(published(), hse_id=hse_id), moscow_today())


@router.get("/programs", response=CatalogPageOut)
def program_list(request: HttpRequest) -> CatalogPageOut:
    return catalog_page(published(), moscow_today())
