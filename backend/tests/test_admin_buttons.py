import re

import pytest
from axes.models import AccessAttempt
from django.utils import timezone
from django_q.models import Task

from catalog.models import Sphere
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

SPHERES_URL = "/admin/catalog/sphere/"
LOCKOUTS_URL = "/admin/protection/lockout/"
TASKS_URL = "/admin/tasks/taskrecord/"
OK = 200
FOUND = 302
FORBIDDEN = 403
ADD_LINK = 'class="addlink'
TO_LIST = "К списку"


@pytest.fixture
def admin_client(client):
    client.force_login(make_admin())
    return client


@pytest.fixture
def sphere():
    return Sphere.objects.create(slug="law", title="Право")


def card(client, url: str, pk: object) -> str:
    response = client.get(f"{url}{pk}/change/")
    assert response.status_code == OK
    return str(response.content.decode())


def test_form_has_single_save_button(admin_client, sphere):
    html = card(admin_client, SPHERES_URL, sphere.pk)
    assert 'name="_save"' in html
    assert 'name="_continue"' not in html
    assert 'name="_addanother"' not in html
    assert 'name="_saveasnew"' not in html


def test_delete_button_is_one_word(admin_client, sphere):
    html = card(admin_client, SPHERES_URL, sphere.pk)
    assert f"{SPHERES_URL}{sphere.pk}/delete/" in html
    assert "Удалить Направление" not in html


def test_add_link_only_in_list(admin_client, sphere):
    assert ADD_LINK in admin_client.get(SPHERES_URL).content.decode()
    assert ADD_LINK not in card(admin_client, SPHERES_URL, sphere.pk)
    assert ADD_LINK not in admin_client.get(f"{SPHERES_URL}add/").content.decode()


def test_save_returns_to_list_with_plain_message(admin_client, sphere):
    form = {"slug": sphere.slug, "title": "Право и суд", "position": 0}
    response = admin_client.post(f"{SPHERES_URL}{sphere.pk}/change/", form, follow=True)
    assert response.redirect_chain[-1] == (SPHERES_URL, FOUND)
    html = response.content.decode()
    assert re.search(r"Сохранено: «<a [^>]+>Право и суд</a>»\.", html)
    assert "был успешно" not in html


def test_delete_message_has_no_broken_gender(admin_client, sphere):
    response = admin_client.post(f"{SPHERES_URL}{sphere.pk}/delete/", {"post": "yes"}, follow=True)
    html = response.content.decode()
    assert "Удалено: «Право»." in html
    assert "был успешно" not in html


def test_lockout_is_view_only(admin_client):
    entry = AccessAttempt.objects.create(username="someone", ip_address="203.0.113.5", failures_since_start=2)
    html = card(admin_client, LOCKOUTS_URL, entry.pk)
    assert 'name="_save"' not in html
    assert TO_LIST in html
    assert f"{LOCKOUTS_URL}{entry.pk}/delete/" in html
    assert admin_client.post(f"{LOCKOUTS_URL}{entry.pk}/change/", {}).status_code == FORBIDDEN


def test_finished_task_is_view_only(admin_client):
    now = timezone.now()
    fields = {"name": "sync", "func": "catalog.tasks.sync", "started": now, "stopped": now, "success": True}
    task = Task.objects.create(id="t1", **fields)
    html = card(admin_client, TASKS_URL, task.pk)
    assert 'name="_save"' not in html
    assert TO_LIST in html
