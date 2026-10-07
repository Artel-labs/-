from datetime import timedelta
from io import StringIO

import pytest
from axes.models import AccessLog
from django.core.management import call_command
from django.utils import timezone
from django_q.models import Schedule

from applications.models import Application, Topic
from tasks.retention import RETENTION_TASKS

pytestmark = pytest.mark.django_db

PURGE_MARK = "purge"


def run() -> list[str]:
    out = StringIO()
    call_command("purge_expired", stdout=out)
    return out.getvalue().splitlines()


def test_every_scheduled_purge_runs_after_restore():
    scheduled = set(Schedule.objects.filter(func__contains=PURGE_MARK).values_list("func", flat=True))
    assert scheduled == set(RETENTION_TASKS)


def test_command_reports_each_purge_by_title():
    assert [line.split(":")[0] for line in run()] == [
        "Удаление старых заявок",
        "Удаление старой аналитики",
        "Удаление старых записей журнала входов",
    ]


def test_command_removes_expired_records(settings):
    settings.APPLICATION_MAX_RETENTION_DAYS = 365
    settings.AXES_LOG_RETENTION_DAYS = 90
    old = Application.objects.create(topic=Topic.FEEDBACK, comment="старая")
    Application.objects.filter(pk=old.pk).update(received_at=timezone.now() - timedelta(days=366))
    fresh = Application.objects.create(topic=Topic.FEEDBACK, comment="новая")
    entry = AccessLog.objects.create(username="old", ip_address="203.0.113.7", user_agent="")
    AccessLog.objects.filter(pk=entry.pk).update(attempt_time=timezone.now() - timedelta(days=91))
    lines = run()
    assert lines[0].startswith("Удаление старых заявок: Удалено заявок: 1")
    assert list(Application.objects.values_list("pk", flat=True)) == [fresh.pk]
    assert not AccessLog.objects.exists()
