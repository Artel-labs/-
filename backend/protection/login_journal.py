from dataclasses import dataclass
from datetime import datetime, timedelta

from axes.models import AccessFailureLog, AccessLog
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from protection.user_agents import short_agent

JOURNAL_LIMIT = 500
PERIODS = {"1": "За сутки", "7": "За неделю", "30": "За месяц"}


class Outcome(models.TextChoices):
    OK = "ok", "Вошёл"
    WRONG = "wrong", "Неверный пароль"
    LOCKED = "locked", "Заблокирован"


@dataclass(frozen=True)
class Row:
    when: datetime
    outcome: Outcome
    username: str
    ip: str
    browser: str


def since(days: str | None) -> datetime | None:
    return timezone.now() - timedelta(days=int(days)) if days in PERIODS else None


def recent(queryset: QuerySet[AccessLog] | QuerySet[AccessFailureLog], start: datetime | None) -> list[object]:
    if start:
        queryset = queryset.filter(attempt_time__gte=start)
    return list(queryset.order_by("-attempt_time")[:JOURNAL_LIMIT])


def sources(start: datetime | None) -> dict[Outcome, list[object]]:
    return {
        Outcome.OK: recent(AccessLog.objects.all(), start),
        Outcome.WRONG: recent(AccessFailureLog.objects.filter(locked_out=False), start),
        Outcome.LOCKED: recent(AccessFailureLog.objects.filter(locked_out=True), start),
    }


def row(outcome: Outcome, entry: AccessLog | AccessFailureLog) -> Row:
    return Row(entry.attempt_time, outcome, entry.username or "", entry.ip_address or "", short_agent(entry.user_agent))


def entries(outcome: str | None, days: str | None) -> list[Row]:
    chosen = {key: items for key, items in sources(since(days)).items() if not outcome or key == outcome}
    rows = [row(key, item) for key, items in chosen.items() for item in items]
    return sorted(rows, key=lambda item: item.when, reverse=True)[:JOURNAL_LIMIT]
