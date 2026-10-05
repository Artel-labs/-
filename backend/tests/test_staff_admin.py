import re
from datetime import timedelta

import pytest
from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.utils import timezone

from accounts import two_factor
from accounts.roles import STAFF_GROUP, Role, apply_role, staff_group
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

USERS_URL = "/admin/auth/user/"
ADD_URL = f"{USERS_URL}add/"
PROGRAMS_URL = "/admin/catalog/program/"
GROUPS_URL = "/admin/auth/group/"
OK = 200
FOUND = 302
FORBIDDEN = 403
NOT_FOUND = 404
STAFF_LOGIN = "editor"
SHOWN_PASSWORD = re.compile(r'id="dpo-password">([^<]+)<')


def card_url(user: User) -> str:
    return f"{USERS_URL}{user.pk}/change/"


def step_url(user: User, path: str) -> str:
    return f"{USERS_URL}{user.pk}/{path}/"


def make_staff(login: str = STAFF_LOGIN) -> User:
    user = User.objects.create_user(login, password="Сотрудник-пароль-2026")
    apply_role(user, Role.STAFF)
    return user


def shown_password(html: str) -> str:
    found = SHOWN_PASSWORD.search(html)
    assert found
    return found.group(1)


def admin_client(client):
    admin = make_admin()
    client.force_login(admin)
    return admin


def test_staff_role_gets_work_sections_only():
    codenames = set(staff_group().permissions.values_list("codename", flat=True))
    assert {"view_program", "change_program", "view_application", "add_mailrecipient", "view_event"} <= codenames
    assert not codenames & {"view_user", "change_user", "view_accessattempt", "view_schedule", "add_application"}


def test_staff_sees_catalog_but_not_users(client):
    client.force_login(make_staff())
    assert client.get(PROGRAMS_URL).status_code == OK
    assert client.get(USERS_URL).status_code == FORBIDDEN


def test_groups_section_is_gone(client):
    admin_client(client)
    assert client.get(GROUPS_URL).status_code == NOT_FOUND


def test_add_form_asks_only_names_and_role(client):
    admin_client(client)
    html = client.get(ADD_URL).content.decode()
    assert 'name="role"' in html
    assert 'name="password1"' not in html
    assert 'name="user_permissions"' not in html
    assert 'name="groups"' not in html


def test_new_staff_gets_password_shown_once(client):
    admin_client(client)
    form = {"username": "new", "first_name": "Анна", "last_name": "Иванова", "role": Role.STAFF}
    response = client.post(ADD_URL, form)
    assert response.status_code == OK
    password = shown_password(response.content.decode())
    user = User.objects.get(username="new")
    assert user.check_password(password)
    assert user.is_staff
    assert not user.is_superuser
    assert list(user.groups.values_list("name", flat=True)) == [STAFF_GROUP]
    assert "no-store" in response["Cache-Control"]


def test_new_admin_role_makes_superuser(client):
    admin_client(client)
    client.post(ADD_URL, {"username": "boss", "role": Role.ADMIN})
    assert User.objects.get(username="boss").is_superuser


def test_card_has_one_save_button_and_login_state(client):
    admin_client(client)
    html = client.get(card_url(make_staff())).content.decode()
    assert "Состояние входа" in html
    assert 'name="_continue"' not in html
    assert 'name="_addanother"' not in html
    assert "pbkdf2" not in html


def test_reset_password_asks_then_shows_new_one(client):
    admin_client(client)
    staff = make_staff()
    assert "Сбросить пароль?" in client.get(step_url(staff, "reset-password")).content.decode()
    password = shown_password(client.post(step_url(staff, "reset-password")).content.decode())
    staff.refresh_from_db()
    assert staff.check_password(password)


def test_disable_and_enable_access(client):
    admin_client(client)
    staff = make_staff()
    assert client.post(step_url(staff, "disable-access")).status_code == FOUND
    staff.refresh_from_db()
    assert not staff.is_active
    client.post(step_url(staff, "enable-access"))
    staff.refresh_from_db()
    assert staff.is_active


def test_cannot_disable_or_delete_yourself(client):
    admin = admin_client(client)
    assert client.post(step_url(admin, "disable-access")).status_code == FORBIDDEN
    assert client.post(f"{USERS_URL}{admin.pk}/delete/", {"post": "yes"}).status_code == FORBIDDEN
    admin.refresh_from_db()
    assert admin.is_active


def test_cannot_demote_yourself_as_last_admin(client):
    admin = admin_client(client)
    response = client.post(card_url(admin), {"username": admin.username, "role": Role.STAFF})
    assert "Это ваша учётная запись" in response.content.decode()
    admin.refresh_from_db()
    assert admin.is_superuser


def test_other_staff_can_be_deleted(client):
    admin_client(client)
    staff = make_staff()
    client.post(f"{USERS_URL}{staff.pk}/delete/", {"post": "yes"})
    assert not User.objects.filter(pk=staff.pk).exists()


def test_two_factor_button_only_when_enabled(client):
    admin_client(client)
    staff = make_staff()
    assert client.get(step_url(staff, "drop-two-factor")).status_code == FORBIDDEN
    device = two_factor.start(staff)
    device.confirmed_at = timezone.now()
    device.save()
    assert "drop-two-factor" in client.get(card_url(staff)).content.decode()
    client.post(step_url(staff, "drop-two-factor"))
    assert not two_factor.is_enabled(staff)


def test_unlock_clears_lockout(client):
    admin_client(client)
    staff = make_staff()
    AccessAttempt.objects.create(
        username=staff.username,
        ip_address="203.0.113.10",
        failures_since_start=settings.LOGIN_FAILURE_LIMIT,
        attempt_time=timezone.now() - timedelta(minutes=1),
    )
    assert "Заблокирован" in client.get(card_url(staff)).content.decode()
    client.post(step_url(staff, "unlock"))
    assert not AccessAttempt.objects.filter(username=staff.username).exists()


def test_user_admin_has_no_raw_permission_lists():
    assert not Permission.objects.filter(group__name=STAFF_GROUP, content_type__app_label="auth").exists()


def test_users_section_speaks_plainly(client):
    admin_client(client)
    html = client.get(USERS_URL).content.decode()
    assert "Пользователи и группы" not in html
    assert "Логин" in html
