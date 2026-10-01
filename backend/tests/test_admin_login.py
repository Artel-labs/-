import pytest
from django.conf import settings

from tests.factories import ADMIN_LOGIN, ADMIN_PASSWORD, make_admin

pytestmark = pytest.mark.django_db

LOGIN_URL = "/admin/login/"
ATTACKER_IP = "203.0.113.10"
OFFICE_IP = "198.51.100.20"
LOCKED = 429


def log_in(client, password, ip=ATTACKER_IP):
    return client.post(LOGIN_URL, {"username": ADMIN_LOGIN, "password": password}, HTTP_X_REAL_IP=ip)


def exhaust_attempts(client):
    for _ in range(settings.LOGIN_FAILURE_LIMIT):
        log_in(client, "неверный-пароль")


def test_login_page_is_shown(client):
    response = client.get(LOGIN_URL)
    assert response.status_code == 200
    assert 'name="username"' in response.content.decode()


def test_admin_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response["Location"].startswith(LOGIN_URL)


def test_admin_can_log_in(client):
    make_admin()
    response = log_in(client, ADMIN_PASSWORD)
    assert response.status_code == 302
    assert response["Location"] == "/admin/"
    assert client.get("/admin/").status_code == 200


def test_repeated_failures_lock_the_address(client):
    make_admin()
    exhaust_attempts(client)
    assert log_in(client, ADMIN_PASSWORD).status_code == LOCKED


def test_lock_does_not_block_other_addresses(client):
    make_admin()
    exhaust_attempts(client)
    assert log_in(client, ADMIN_PASSWORD, ip=OFFICE_IP).status_code == 302
