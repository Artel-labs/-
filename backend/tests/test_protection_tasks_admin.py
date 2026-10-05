from datetime import timedelta

import pytest
from axes.models import AccessAttempt, AccessFailureLog, AccessLog
from django.conf import settings
from django.utils import timezone
from django_q.models import OrmQ, Schedule, Task

from protection.lockout import status
from protection.user_agents import short_agent
from tests.factories import make_admin
from tests.test_staff_admin import make_staff

pytestmark = pytest.mark.django_db

LOCKOUTS = "/admin/protection/lockout/"
JOURNAL = "/admin/protection/loginjournal/"
SCHEDULE = "/admin/tasks/plannedtask/"
TASKS = "/admin/tasks/taskrecord/"
OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
CHROME_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/18.0 Mobile/15E148 Safari/604.1"
)
ANDROID_CHROME = (
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Mobile Safari/537.36"
)


@pytest.fixture
def admin_client(client):
    client.force_login(make_admin())
    return client


def attempt(failures: int, minutes_ago: int = 1, username: str = "anna") -> AccessAttempt:
    entry = AccessAttempt.objects.create(
        username=username, ip_address="203.0.113.7", user_agent=CHROME_WINDOWS, failures_since_start=failures
    )
    AccessAttempt.objects.filter(pk=entry.pk).update(attempt_time=timezone.now() - timedelta(minutes=minutes_ago))
    entry.refresh_from_db()
    return entry


def page(client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == OK
    return str(response.content.decode())


@pytest.mark.parametrize(
    ("agent", "label"),
    [
        (CHROME_WINDOWS, "Chrome, Windows"),
        (SAFARI_IPHONE, "Safari, iOS"),
        (ANDROID_CHROME, "Chrome, Android"),
        ("", "неизвестно"),
    ],
)
def test_short_agent(agent, label):
    assert short_agent(agent) == label


def test_lockout_status_texts():
    assert status(attempt(settings.LOGIN_FAILURE_LIMIT)).startswith("Заблокирован до ")
    assert status(attempt(2, username="ivan")) == "Ошибок: 2"
    expired = int(settings.LOGIN_COOLOFF.total_seconds() // 60) + 5
    old = attempt(settings.LOGIN_FAILURE_LIMIT, minutes_ago=expired, username="oleg")
    assert status(old) == f"Ошибок: {settings.LOGIN_FAILURE_LIMIT}"


def test_lockout_list_is_russian(admin_client):
    attempt(settings.LOGIN_FAILURE_LIMIT)
    html = page(admin_client, LOCKOUTS)
    assert "Заблокирован до" in html
    assert "Chrome, Windows" in html
    assert "Locked Out" not in html
    assert "Clean up expired attempts" not in html


def test_unlock_action_removes_lockout(admin_client):
    entry = attempt(settings.LOGIN_FAILURE_LIMIT)
    form = {"action": "unlock_selected", "index": "0", "_selected_action": [str(entry.pk)]}
    response = admin_client.post(LOCKOUTS, form, follow=True)
    assert "Блокировка снята: 1." in response.content.decode()
    assert not AccessAttempt.objects.filter(pk=entry.pk).exists()


def test_journal_merges_logins_and_failures(admin_client):
    AccessLog.objects.create(username="anna", ip_address="203.0.113.7", user_agent=CHROME_WINDOWS)
    AccessFailureLog.objects.create(username="ivan", ip_address="203.0.113.8", user_agent=SAFARI_IPHONE)
    AccessFailureLog.objects.create(username="oleg", ip_address="203.0.113.9", user_agent="", locked_out=True)
    html = page(admin_client, JOURNAL)
    for text in ("Вошёл", "Неверный пароль", "Заблокирован", "Safari, iOS", "anna", "ivan", "oleg"):
        assert text in html
    assert "Access Log for" not in html


def test_journal_filters_by_outcome(admin_client):
    AccessLog.objects.create(username="anna", ip_address="203.0.113.7", user_agent="")
    AccessFailureLog.objects.create(username="ivan", ip_address="203.0.113.8", user_agent="")
    html = page(admin_client, f"{JOURNAL}?outcome=ok&days=7")
    assert "anna" in html
    assert "ivan" not in html


def test_schedule_is_readable(admin_client):
    html = page(admin_client, SCHEDULE)
    assert "Обновление каталога с hse.ru" in html
    assert "каждый день в 04:00" in html
    assert "Запустить сейчас" in html
    assert "catalog.tasks.sync_catalog" not in html
    assert f"{SCHEDULE}add/" not in html


def test_run_now_queues_once(admin_client):
    schedule = Schedule.objects.get(func="catalog.tasks.sync_catalog")
    url = f"{SCHEDULE}{schedule.pk}/run/"
    admin_client.post(url)
    response = admin_client.post(url, follow=True)
    assert OrmQ.objects.count() == 1
    assert "уже выполняется" in response.content.decode()
    assert admin_client.get(url).status_code == FORBIDDEN


def test_task_journal_names_and_outcomes(admin_client):
    now = timezone.now()
    Task.objects.create(
        id="a1",
        name="michigan-snake-asparagus-north",
        func="catalog.tasks.sync_catalog",
        started=now - timedelta(seconds=75),
        stopped=now,
        success=False,
        result="[Errno 111] Connection refused : Traceback (most recent call last):",
    )
    html = page(admin_client, TASKS)
    assert "Обновление каталога с hse.ru" in html
    assert "michigan-snake" not in html
    assert "Ошибка" in html
    assert "1 мин 15 с" in html
    assert "[Errno 111] Connection refused<" in html.replace("\n", "").replace("  ", "")


def test_staff_role_does_not_see_protection_or_tasks(client):
    client.force_login(make_staff())
    for url in (LOCKOUTS, JOURNAL, SCHEDULE, TASKS):
        assert client.get(url).status_code == FORBIDDEN


@pytest.mark.parametrize("url", ["/admin/axes/accesslog/", "/admin/django_q/success/", "/admin/django_q/ormq/"])
def test_old_technical_pages_are_gone(admin_client, url):
    assert admin_client.get(url).status_code == NOT_FOUND
