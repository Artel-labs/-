import time
from io import StringIO
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts import pending_login, two_factor
from accounts.models import TwoFactor
from accounts.pending_login import PENDING_SECONDS
from accounts.totp import code_at, current_step, decode, matching_step, provisioning_uri
from tests.factories import ADMIN_LOGIN, ADMIN_PASSWORD, make_admin

pytestmark = pytest.mark.django_db

LOGIN_URL = "/admin/login/"
CODE_URL = "/admin/login/code/"
INDEX_URL = "/admin/"
SETTINGS_URL = "/admin/accounts/twofactor/"
IP = "203.0.113.10"
OK = 200
RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
LOCKED = 429


def code_now(secret: str, shift: int = 0) -> str:
    return code_at(decode(secret), current_step(time.time()) + shift)


def log_in(client, ip: str = IP, url: str = LOGIN_URL):
    return client.post(url, {"username": ADMIN_LOGIN, "password": ADMIN_PASSWORD}, HTTP_X_REAL_IP=ip)


def send_code(client, code: str, ip: str = IP):
    return client.post(CODE_URL, {"code": code}, HTTP_X_REAL_IP=ip)


def logged_in(client) -> bool:
    return bool(client.get(INDEX_URL).status_code == OK)


def enable_for(admin) -> TwoFactor:
    device = two_factor.start(admin)
    assert two_factor.confirm(admin, code_now(device.secret, -1))
    device.refresh_from_db()
    return device


def test_codes_match_rfc_6238_vectors():
    key = decode(RFC_SECRET)
    assert code_at(key, 59 // 30) == "287082"
    assert code_at(key, 1111111109 // 30) == "081804"
    assert code_at(key, 1234567890 // 30) == "005924"


def test_window_and_replay_protection():
    now = 1234567890.0
    step = current_step(now)
    code = code_at(decode(RFC_SECRET), step - 1)
    assert matching_step(RFC_SECRET, code, now, 0) == step - 1
    assert matching_step(RFC_SECRET, code, now, step - 1) is None
    assert matching_step(RFC_SECRET, code_at(decode(RFC_SECRET), step - 2), now, 0) is None
    assert matching_step(RFC_SECRET, "12ab56", now, 0) is None


def test_provisioning_uri_names_issuer_and_account():
    uri = provisioning_uri(RFC_SECRET, "admin")
    assert uri.startswith("otpauth://totp/")
    assert f"secret={RFC_SECRET}" in uri
    assert "issuer=" in uri


def test_login_page_has_no_code_field(client):
    assert "Код из приложения" not in client.get(LOGIN_URL).content.decode()


def test_login_without_two_factor_needs_only_password(client):
    make_admin()
    response = log_in(client)
    assert response.status_code == 302
    assert response["Location"] == INDEX_URL
    assert logged_in(client)


def test_enabled_two_factor_asks_code_on_separate_page(client):
    device = enable_for(make_admin())
    response = log_in(client)
    assert response["Location"] == CODE_URL
    assert not logged_in(client)
    page = client.get(CODE_URL).content.decode()
    assert "Код из приложения" in page
    assert "Неверный код" in send_code(client, "000000").content.decode()
    assert not logged_in(client)
    assert send_code(client, code_now(device.secret))["Location"] == INDEX_URL
    assert logged_in(client)


def test_wrong_password_never_reaches_code_page(client):
    enable_for(make_admin())
    response = client.post(LOGIN_URL, {"username": ADMIN_LOGIN, "password": "неверный"}, HTTP_X_REAL_IP=IP)
    assert response.status_code == OK
    assert client.get(CODE_URL)["Location"] == LOGIN_URL


def test_code_page_without_password_step_redirects_to_login(client):
    assert client.get(CODE_URL)["Location"] == LOGIN_URL
    assert send_code(client, "000000")["Location"] == LOGIN_URL


def test_password_step_expires(client, monkeypatch):
    device = enable_for(make_admin())
    log_in(client)
    late = time.time() + PENDING_SECONDS + 1
    monkeypatch.setattr(pending_login, "time", SimpleNamespace(time=lambda: late))
    assert send_code(client, code_now(device.secret))["Location"] == LOGIN_URL
    assert not logged_in(client)


def test_next_address_is_kept_through_code_step(client):
    device = enable_for(make_admin())
    log_in(client, url=f"{LOGIN_URL}?next={SETTINGS_URL}")
    assert send_code(client, code_now(device.secret))["Location"] == SETTINGS_URL


def test_code_cannot_be_reused(client):
    device = enable_for(make_admin())
    code = code_now(device.secret)
    log_in(client)
    send_code(client, code)
    client.logout()
    log_in(client)
    assert "Неверный код" in send_code(client, code).content.decode()
    assert not logged_in(client)


def test_wrong_codes_lock_the_address(client):
    enable_for(make_admin())
    log_in(client)
    for _ in range(settings.LOGIN_FAILURE_LIMIT - 1):
        assert send_code(client, "000000").status_code == OK
    assert send_code(client, "000000").status_code == LOCKED
    assert log_in(client).status_code == LOCKED


def test_account_menu_links_to_two_factor_settings(client):
    client.force_login(make_admin())
    assert f'href="{SETTINGS_URL}"' in client.get(INDEX_URL).content.decode()


def test_settings_page_enables_and_disables(client):
    admin = make_admin()
    client.force_login(admin)
    assert "выключен" in client.get(SETTINGS_URL).content.decode()
    client.post(SETTINGS_URL, {"action": "start"})
    device = TwoFactor.objects.get(user=admin)
    page = client.get(SETTINGS_URL).content.decode()
    assert "otpauth://totp/" in page
    assert "Неверный код" in client.post(SETTINGS_URL, {"action": "confirm", "code": "000000"}).content.decode()
    assert client.post(SETTINGS_URL, {"action": "confirm", "code": code_now(device.secret)}).status_code == 302
    assert two_factor.is_enabled(admin)
    assert client.post(SETTINGS_URL, {"action": "disable", "code": code_now(device.secret, 1)}).status_code == 302
    assert not two_factor.is_enabled(admin)


def test_restart_replaces_unconfirmed_secret():
    admin = make_admin()
    first = two_factor.start(admin).secret
    assert two_factor.start(admin).secret != first


def test_command_disables_two_factor():
    admin = make_admin()
    enable_for(admin)
    out = StringIO()
    call_command("disable_two_factor", ADMIN_LOGIN, stdout=out)
    assert "отключён" in out.getvalue()
    assert not two_factor.is_enabled(admin)


def test_command_without_login_disables_the_only_protected_user():
    admin = make_admin()
    enable_for(admin)
    out = StringIO()
    call_command("disable_two_factor", stdout=out)
    assert ADMIN_LOGIN in out.getvalue()
    assert not two_factor.is_enabled(admin)


def test_command_without_login_and_protection_fails():
    make_admin()
    with pytest.raises(CommandError, match="ни у одного"):
        call_command("disable_two_factor")
