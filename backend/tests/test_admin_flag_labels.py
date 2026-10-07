import pytest
from django.contrib.auth.models import User

from catalog.models import Program, Source, Teacher

pytestmark = pytest.mark.django_db

PROGRAMS_URL = "/admin/catalog/program/"
TEACHERS_URL = "/admin/catalog/teacher/"
USERS_URL = "/admin/auth/user/"
OK = 200


def page(client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == OK
    return str(response.content.decode())


def make_program(hse_id: str, title: str, **fields) -> Program:
    defaults = {"type_short": "ПК", "type_title": "ПК", "study_format": "Очный", "source": Source.HSE}
    return Program.objects.create(hse_id=hse_id, title=title, **{**defaults, **fields})


@pytest.fixture
def programs():
    make_program("1", "Следит за hse.ru")
    make_program("2", "Правится вручную", locked=True)
    make_program("3", "Добавлена вручную", source=Source.MANUAL)


def test_program_list_says_what_is_updated_from_hse(admin_client, programs):
    html = page(admin_client, PROGRAMS_URL)
    assert "Обновляется с hse.ru" in html
    assert "Не обновлять с hse.ru" not in html


def test_program_filter_keeps_only_updated_from_hse(admin_client, programs):
    html = page(admin_client, f"{PROGRAMS_URL}?updates=yes")
    assert "Следит за hse.ru" in html
    assert "Правится вручную" not in html
    assert "Добавлена вручную" not in html


def test_program_filter_keeps_manual_programs(admin_client, programs):
    html = page(admin_client, f"{PROGRAMS_URL}?updates=no")
    assert "Следит за hse.ru" not in html
    assert "Правится вручную" in html
    assert "Добавлена вручную" in html


def test_teacher_list_uses_positive_landing_flag(admin_client):
    Teacher.objects.create(name="Иванов Иван Иванович")
    html = page(admin_client, TEACHERS_URL)
    assert "Показывать на главной" in html
    assert "Не показывать на главной" not in html


def test_new_teacher_is_shown_on_landing():
    assert Teacher.objects.create(name="Петров Пётр Петрович").show_on_landing


def test_staff_access_filter_matches_access_column(admin_client):
    User.objects.create_user("blocked", is_staff=True, is_active=False)
    html = page(admin_client, USERS_URL)
    assert "Включён" in html
    assert "Отключён" in html
    assert "активный" not in html
    filtered = page(admin_client, f"{USERS_URL}?access=off")
    assert "blocked" in filtered
