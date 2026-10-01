import pytest

pytestmark = pytest.mark.django_db


def test_responses_forbid_framing_and_sniffing(client):
    response = client.get("/admin/login/")
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"


def test_session_cookie_is_http_only(client, settings):
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_HTTPONLY is True
