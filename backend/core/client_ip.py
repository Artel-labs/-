from django.http import HttpRequest

PROXY_HEADER = "HTTP_X_REAL_IP"
DIRECT_HEADER = "REMOTE_ADDR"


def client_ip(request: HttpRequest) -> str | None:
    return request.META.get(PROXY_HEADER) or request.META.get(DIRECT_HEADER)
