from datetime import datetime

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from applications.models import Application


def application_history() -> QuerySet[LogEntry]:
    return LogEntry.objects.filter(content_type=ContentType.objects.get_for_model(Application))


def forget_history(application_ids: list[int], older_than: datetime) -> int:
    removed = [str(application_id) for application_id in application_ids]
    stale = application_history().filter(object_id__in=removed) | application_history().filter(
        action_time__lt=older_than
    )
    deleted, _ = stale.delete()
    return deleted
