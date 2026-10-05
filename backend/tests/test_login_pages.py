from pathlib import Path

import pytest
from django.conf import settings

from accounts.forms import WRONG_CODE
from accounts.login_texts import locked_message
from accounts.totp import DIGITS
from tests.factories import ADMIN_LOGIN, make_admin
from tests.test_two_factor import CODE_URL, INDEX_URL, IP, LOGIN_URL, code_now, enable_for, log_in, logged_in

pytestmark = pytest.mark.django_db

OK = 200
REJECTED = 400
LOCKED = 429
SCRIPT = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
REPO = Path(settings.BASE_DIR).parent
BRAND_COPIES = {
    "pattern-cover.svg": "frontend/public/images/pattern-cover.svg",
    "hse-mark.svg": "frontend/public/images/logo/hse-mark.svg",
}


def send_code_from_script(client, code: str):
    return client.post(CODE_URL, {"code": code}, HTTP_X_REAL_IP=IP, **SCRIPT)


def wrong_password(client):
    return client.post(LOGIN_URL, {"username": ADMIN_LOGIN, "password": "неверный"}, HTTP_X_REAL_IP=IP)


def test_login_page_is_glass_card_with_password_toggle(client):
    page = client.get(LOGIN_URL).content.decode()
    assert "accounts/login.css" in page
    assert "accounts/hse-mark.svg" in page
    assert 'name="username"' in page
    assert 'autocomplete="current-password"' in page
    assert "data-secret-toggle" in page


def test_wrong_password_shakes_card_and_shows_error(client):
    make_admin()
    response = wrong_password(client)
    page = response.content.decode()
    assert response.status_code == OK
    assert "is-shaking" in page
    assert 'role="alert"' in page


def test_code_page_tells_script_digits_and_lock_text(client):
    enable_for(make_admin())
    log_in(client)
    page = client.get(CODE_URL).content.decode()
    assert f'data-digits="{DIGITS}"' in page
    assert f'data-locked-message="{locked_message()}"' in page
    assert 'autocomplete="one-time-code"' in page


def test_script_gets_address_after_right_code(client):
    device = enable_for(make_admin())
    log_in(client)
    response = send_code_from_script(client, code_now(device.secret))
    assert response.status_code == OK
    assert response.json() == {"redirect": INDEX_URL}
    assert logged_in(client)


def test_script_gets_error_after_wrong_code(client):
    enable_for(make_admin())
    log_in(client)
    response = send_code_from_script(client, "000000")
    assert response.status_code == REJECTED
    assert response.json() == {"error": WRONG_CODE}
    assert not logged_in(client)


def test_script_learns_about_lock(client):
    enable_for(make_admin())
    log_in(client)
    for _ in range(settings.LOGIN_FAILURE_LIMIT - 1):
        assert send_code_from_script(client, "000000").status_code == REJECTED
    response = send_code_from_script(client, "000000")
    assert response.status_code == LOCKED
    assert response["Content-Type"].startswith("application/json")


def test_lock_page_explains_wait(client):
    make_admin()
    for _ in range(settings.LOGIN_FAILURE_LIMIT):
        wrong_password(client)
    response = wrong_password(client)
    page = response.content.decode()
    assert response.status_code == LOCKED
    assert "Вход заблокирован" in page
    assert locked_message() in page


def test_lock_text_names_cooloff_minutes():
    minutes = int(settings.LOGIN_COOLOFF.total_seconds() // 60)
    assert f"{minutes}\u00a0мин." in locked_message()


@pytest.mark.parametrize(("name", "source"), BRAND_COPIES.items())
def test_brand_files_match_site(name, source):
    copy = Path(settings.BASE_DIR) / "accounts" / "static" / "accounts" / name
    assert copy.read_bytes() == (REPO / source).read_bytes()
