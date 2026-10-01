from django.conf import settings
from ninja import NinjaAPI

from core.api import router as core_router

api = NinjaAPI(
    title="Центр ДПО",
    docs_url="/docs" if settings.DEBUG else None,
)
api.add_router("", core_router)
