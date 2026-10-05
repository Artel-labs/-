import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission

from core.navigation import SECTIONS, model_of
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

INDEX_URL = "/admin/"
STAFF_PASSWORD = "Staff-password-2026"
SECTION_ORDER = ("Заявки", "Каталог программ", "Аналитика", "Пользователи", "Защита входа", "Фоновые задачи")


def listed_models() -> list[str]:
    return [model_of(entry)._meta.label for section in SECTIONS for entry in section.entries]


def page(client) -> str:
    content: bytes = client.get(INDEX_URL).content
    return content.decode()


def test_every_admin_section_is_in_menu_once():
    registered = sorted(model._meta.label for model in admin.site._registry)
    assert sorted(listed_models()) == registered


def test_sections_go_in_working_order():
    assert tuple(section.title for section in SECTIONS) == SECTION_ORDER


def test_index_shows_tiles_and_menu_in_same_order(client):
    client.force_login(make_admin())
    html = page(client)
    tiles = html.split('class="dpo-tiles"')[1]
    positions = [tiles.index(title) for title in SECTION_ORDER]
    assert positions == sorted(positions)
    assert html.count('class="dpo-nav-title"') == len(SECTION_ORDER)
    assert 'href="/admin/catalog/program/add/"' in tiles


def test_staff_sees_only_permitted_sections(client, django_user_model):
    staff = django_user_model.objects.create_user("editor", password=STAFF_PASSWORD, is_staff=True)
    staff.user_permissions.add(Permission.objects.get(codename="view_program"))
    client.force_login(staff)
    tiles = page(client).split('class="dpo-tiles"')[1]
    assert "Каталог программ" in tiles
    assert "Заявки" not in tiles
    assert "/admin/catalog/program/add/" not in tiles


def test_menu_has_collapse_button_and_header_reopen(client):
    client.force_login(make_admin())
    html = page(client)
    assert "dpo-nav-collapse" in html
    assert "dpo-toggle-desktop" in html


def test_current_page_opens_its_folded_section(client):
    client.force_login(make_admin())
    content: bytes = client.get("/admin/django_q/success/").content
    tasks = content.decode().split("dpo-nav-tasks")[1].split("</ol>")[0]
    assert 'x-init="navigationOpen = true"' in tasks
    assert 'href="/admin/django_q/success/"' in tasks.split(" active")[0].rsplit("<a", 1)[1]
