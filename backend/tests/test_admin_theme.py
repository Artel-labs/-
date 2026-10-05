from pathlib import Path

import pytest
from django.conf import settings

from tests.factories import make_admin

pytestmark = pytest.mark.django_db

INDEX_URL = "/admin/"
LOGIN_URL = "/admin/login/"
ADMIN_STYLES = ("accounts/brand.", "accounts/admin.")
HSE_MARK = "accounts/hse-mark."
OLD_ICON = "brand-mark"
THEME_OPTIONS = 3


def admin_page(client) -> str:
    client.force_login(make_admin())
    content: bytes = client.get(INDEX_URL).content
    return content.decode()


def test_admin_pages_load_glass_styles(client):
    page = admin_page(client)
    for style in ADMIN_STYLES:
        assert style in page


def test_admin_corner_shows_hse_mark_with_caption(client):
    page = admin_page(client)
    assert HSE_MARK in page
    assert "факультета права" in page
    assert OLD_ICON not in page


def test_login_page_shares_brand_colors(client):
    assert ADMIN_STYLES[0] in client.get(LOGIN_URL).content.decode()


def test_glass_surfaces_leave_checkboxes_alone():
    css = (Path(settings.BASE_DIR) / "accounts" / "static" / "accounts" / "admin.css").read_text()
    assert "#page #main .bg-white:not(input)" in css
    assert "html.dark #page #main .dark\\:bg-base-900:not(input)" in css


def test_theme_switch_fits_user_menu(client):
    client.force_login(make_admin())
    html = client.get("/admin/").content.decode()
    assert "dpo-theme-switch" in html
    assert html.count('class="dpo-theme-option"') == THEME_OPTIONS
    assert "Как в системе" in html
