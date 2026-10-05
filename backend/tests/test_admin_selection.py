import pytest

from catalog.models import Sphere
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

SPHERES_URL = "/admin/catalog/sphere/"
USERS_URL = "/admin/auth/user/"
TOGGLE = "data-select-toggle"
SCRIPT = "accounts/lists."


@pytest.fixture
def admin_client(client):
    client.force_login(make_admin())
    return client


@pytest.fixture
def spheres():
    return [Sphere.objects.create(slug=f"s{index}", title=f"Направление {index}") for index in range(2)]


def page(client, url: str) -> str:
    return str(client.get(url).content.decode())


def test_list_with_actions_has_select_button_and_action_buttons(admin_client, spheres):
    html = page(admin_client, SPHERES_URL)
    assert TOGGLE in html
    assert 'data-action="delete_selected"' in html
    assert '<input type="hidden" name="action" value="">' in html
    assert 'name="index"' in html
    assert '<select name="action"' not in html
    assert "Выбрать" in html


def test_list_without_actions_has_no_select_button(admin_client):
    assert TOGGLE not in page(admin_client, USERS_URL)


def test_list_script_is_loaded(admin_client):
    assert SCRIPT in page(admin_client, SPHERES_URL)


def test_action_button_runs_action(admin_client, spheres):
    form = {"action": "delete_selected", "index": "0", "_selected_action": [str(spheres[0].pk)]}
    html = admin_client.post(SPHERES_URL, form).content.decode()
    assert "Удалить выбранные записи?" in html
    assert "удалить Направление" not in html


def test_single_delete_question_has_no_broken_gender(admin_client, spheres):
    html = page(admin_client, f"{SPHERES_URL}{spheres[0].pk}/delete/")
    assert "Удалить «Направление 0»?" in html
