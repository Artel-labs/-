import json
from typing import Any

from django.http import HttpRequest, HttpResponse
from ninja import Router

from analytics.service import ingest
from core.origin import same_origin

router = Router(tags=["Аналитика"])

NO_CONTENT = 204
BAD_REQUEST = 400
FORBIDDEN = 403


def events_of(payload: Any) -> Any:
    return payload.get("events") if isinstance(payload, dict) else payload


@router.post("", include_in_schema=False)
def collect(request: HttpRequest) -> HttpResponse:
    if not same_origin(request):
        return HttpResponse(status=FORBIDDEN)
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=BAD_REQUEST)
    ingest(events_of(payload))
    return HttpResponse(status=NO_CONTENT)
