from django.test import RequestFactory

from core.client_ip import client_ip

PROXY_IP = "172.18.0.4"
VISITOR_IP = "203.0.113.7"


def test_proxy_header_wins():
    request = RequestFactory().get("/", REMOTE_ADDR=PROXY_IP, HTTP_X_REAL_IP=VISITOR_IP)
    assert client_ip(request) == VISITOR_IP


def test_direct_address_is_fallback():
    request = RequestFactory().get("/", REMOTE_ADDR=VISITOR_IP)
    assert client_ip(request) == VISITOR_IP
