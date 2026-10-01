from django.http import HttpRequest
from ninja import Router, Status

from applications.parsing import parse
from applications.schemas import AcceptedOut, ApplicationIn, FieldErrorOut, RejectedOut
from applications.service import accept
from core.origin import same_origin

router = Router(tags=["Заявки"])

OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403


@router.post("", response={OK: AcceptedOut, BAD_REQUEST: RejectedOut, FORBIDDEN: RejectedOut})
def submit(request: HttpRequest, data: ApplicationIn) -> Status[AcceptedOut | RejectedOut]:
    if not same_origin(request):
        return Status(FORBIDDEN, RejectedOut(error="origin not allowed"))
    if isinstance(data.website, str) and data.website.strip():
        return Status(OK, AcceptedOut(ok=True))
    parsed = parse(data)
    if parsed.cleaned is None:
        fields = [FieldErrorOut(field=error.field, message=error.message) for error in parsed.errors]
        return Status(BAD_REQUEST, RejectedOut(error="validation", fields=fields))
    accepted = accept(parsed.cleaned)
    return Status(OK, AcceptedOut(ok=True, id=accepted.id))
