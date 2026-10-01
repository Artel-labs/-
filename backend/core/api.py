from django.conf import settings
from django.http import HttpRequest
from ninja import Router, Schema, Status

from core.health import database_ready
from core.site import SHARE_IMAGE_PATH, absolute_url

router = Router(tags=["Служебное"])

READY = "ok"
DATABASE_DOWN = "database-unavailable"


class HealthOut(Schema):
    status: str


@router.get("/health", response={200: HealthOut, 503: HealthOut})
def health(request: HttpRequest) -> Status[HealthOut]:
    if database_ready():
        return Status(200, HealthOut(status=READY))
    return Status(503, HealthOut(status=DATABASE_DOWN))


class SiteOut(Schema):
    site_url: str
    image_url: str


@router.get("/site", response=SiteOut)
def site(request: HttpRequest) -> SiteOut:
    return SiteOut(site_url=settings.SITE_URL, image_url=absolute_url(SHARE_IMAGE_PATH))
