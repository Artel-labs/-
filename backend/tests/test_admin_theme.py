import pytest

from tests.factories import make_admin

pytestmark = pytest.mark.django_db

INDEX_URL = "/admin/"
LOGIN_URL = "/admin/login/"
ADMIN_STYLES = ("accounts/brand.", "accounts/admin.")
HSE_MARK = "accounts/hse-mark."
OLD_ICON = "brand-mark"


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
