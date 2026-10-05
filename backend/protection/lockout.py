from datetime import datetime

from axes.models import AccessAttempt
from axes.utils import reset
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

LOCKED_TEXT = "Заблокирован до {until}"
FAILURES_TEXT = "Ошибок: {count}"
TIME_FORMAT = "%H:%M"


def recent_since() -> datetime:
    return timezone.now() - settings.LOGIN_COOLOFF


def locked_attempts() -> QuerySet[AccessAttempt]:
    attempts: QuerySet[AccessAttempt] = AccessAttempt.objects.filter(
        attempt_time__gte=recent_since(), failures_since_start__gte=settings.LOGIN_FAILURE_LIMIT
    )
    return attempts


def is_locked(attempt: AccessAttempt) -> bool:
    return bool(attempt.failures_since_start >= settings.LOGIN_FAILURE_LIMIT and attempt.attempt_time >= recent_since())


def locked_until(attempt: AccessAttempt) -> datetime:
    return timezone.localtime(attempt.attempt_time + settings.LOGIN_COOLOFF)


def status(attempt: AccessAttempt) -> str:
    if is_locked(attempt):
        return LOCKED_TEXT.format(until=locked_until(attempt).strftime(TIME_FORMAT))
    return FAILURES_TEXT.format(count=attempt.failures_since_start)


def unlock(username: str, ip: str | None = None) -> None:
    reset(ip=ip, username=username)
