from django.conf import settings
from ninja import NinjaAPI

from applications.api import router as applications_router
from catalog.api import router as catalog_router
from core.api import router as core_router

api = NinjaAPI(
    title="Центр ДПО",
    docs_url="/docs" if settings.DEBUG else None,
)
api.add_router("", core_router)
api.add_router("/catalog", catalog_router)
api.add_router("/applications", applications_router)
