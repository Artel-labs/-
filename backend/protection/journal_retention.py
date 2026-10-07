from datetime import timedelta

from axes.models import AccessFailureLog, AccessLog
from django.conf import settings
from django.utils import timezone


def purge_old_journal() -> str:
    cutoff = timezone.now() - timedelta(days=settings.AXES_LOG_RETENTION_DAYS)
    entries, _ = AccessLog.objects.filter(attempt_time__lt=cutoff).delete()
    failures, _ = AccessFailureLog.objects.filter(attempt_time__lt=cutoff).delete()
    return (
        f"Удалено из журнала входов старше {settings.AXES_LOG_RETENTION_DAYS} дн.: "
        f"входов {entries}, неудачных попыток {failures}"
    )
