from urllib.parse import urlsplit

from django.http import HttpRequest


def same_origin(request: HttpRequest) -> bool:
    origin = request.headers.get("Origin")
    return not origin or urlsplit(origin).netloc == request.get_host()
