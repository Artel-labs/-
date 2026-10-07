from datetime import timedelta

import pytest
from axes.models import AccessFailureLog, AccessLog
from django.utils import timezone
from django_q.models import Schedule

from protection.journal_retention import purge_old_journal

pytestmark = pytest.mark.django_db


def aged(model: type[AccessLog] | type[AccessFailureLog], username: str, days: int) -> None:
    entry = model.objects.create(username=username, ip_address="203.0.113.7", user_agent="")
    model.objects.filter(pk=entry.pk).update(attempt_time=timezone.now() - timedelta(days=days))


def test_purge_removes_only_entries_older_than_retention(settings):
    settings.AXES_LOG_RETENTION_DAYS = 90
    aged(AccessLog, "old", 91)
    aged(AccessLog, "fresh", 89)
    aged(AccessFailureLog, "old-failure", 91)
    aged(AccessFailureLog, "fresh-failure", 10)
    assert purge_old_journal() == "Удалено из журнала входов старше 90 дн.: входов 1, неудачных попыток 1"
    assert list(AccessLog.objects.values_list("username", flat=True)) == ["fresh"]
    assert list(AccessFailureLog.objects.values_list("username", flat=True)) == ["fresh-failure"]


def test_journal_purge_is_scheduled_daily():
    schedule = Schedule.objects.get(func="protection.tasks.purge_login_journal")
    assert schedule.schedule_type == Schedule.DAILY
