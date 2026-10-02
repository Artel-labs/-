from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task, schedule

SEND_MAIL_TASK = "applications.mail.send_application_mail"


def queue_mail(application_id: int) -> None:
    async_task(SEND_MAIL_TASK, application_id, task_name=f"Письмо по заявке № {application_id}")


def retry_name(application_id: int, attempt: int) -> str:
    return f"Повтор письма по заявке № {application_id}, попытка {attempt}"


def schedule_retry(application_id: int, attempt: int) -> None:
    name = retry_name(application_id, attempt)
    if Schedule.objects.filter(name=name).exists():
        return
    schedule(
        SEND_MAIL_TASK,
        application_id,
        name=name,
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + timedelta(minutes=settings.APPLICATION_MAIL_RETRY_MINUTES),
    )
