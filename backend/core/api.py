from django.http import HttpRequest
from ninja import Router, Schema, Status

from core.health import database_ready

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
