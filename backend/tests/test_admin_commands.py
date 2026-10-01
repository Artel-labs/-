from io import StringIO

import pytest
from axes.models import AccessAttempt
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.passwords import GENERATED_PASSWORD_LENGTH
from tests.factories import ADMIN_LOGIN, make_admin

pytestmark = pytest.mark.django_db


def run(*args):
    output = StringIO()
    call_command(*args, stdout=output)
    return output.getvalue()


def shown_password(output):
    line = next(line for line in output.splitlines() if line.startswith("Пароль:"))
    return line.split(":", 1)[1].strip()


def test_first_admin_is_created_with_strong_password():
    output = run("create_admin")
    admin = User.objects.get(username="admin")
    password = shown_password(output)
    assert admin.is_superuser
    assert admin.is_staff
    assert len(password) == GENERATED_PASSWORD_LENGTH
    assert admin.check_password(password)


def test_existing_admin_is_kept():
    make_admin()
    output = run("create_admin")
    assert "уже есть" in output
    assert User.objects.count() == 1


def test_reset_sets_new_password_and_unlocks():
    admin = make_admin()
    AccessAttempt.objects.create(username=ADMIN_LOGIN, ip_address="203.0.113.10", failures_since_start=5)
    password = shown_password(run("reset_admin_password", ADMIN_LOGIN))
    admin.refresh_from_db()
    assert admin.check_password(password)
    assert not AccessAttempt.objects.filter(username=ADMIN_LOGIN).exists()


def test_reset_unknown_login_fails():
    with pytest.raises(CommandError, match="нет"):
        run("reset_admin_password", "nobody")
