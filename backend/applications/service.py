from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django_q.tasks import async_task

from applications.mail import mail_configured
from applications.models import Application, MailStatus
from applications.parsing import Cleaned
from catalog.models import Program

SEND_MAIL_TASK = "applications.mail.send_application_mail"
MAIL_TASK_NAME = "Письмо по заявке"


@dataclass(frozen=True)
class Accepted:
    id: int
    duplicate: bool


def duplicate_key(cleaned: Cleaned) -> str:
    digits = "".join(char for char in cleaned.phone if char.isdigit())
    return "|".join((cleaned.topic, cleaned.email.lower(), digits, cleaned.program_id))


def recent_duplicate(key: str) -> Application | None:
    since = timezone.now() - timedelta(minutes=settings.APPLICATION_DUPLICATE_MINUTES)
    return Application.objects.filter(duplicate_key=key, received_at__gte=since).first()


def program_for(program_id: str) -> Program | None:
    return Program.objects.filter(hse_id=program_id).first() if program_id else None


def create(cleaned: Cleaned, key: str) -> Application:
    program = program_for(cleaned.program_id)
    fields = {name: value for name, value in cleaned.__dict__.items() if name not in ("program_id", "program_title")}
    return Application.objects.create(
        **fields,
        program=program,
        program_title=program.title if program else cleaned.program_title,
        mail_status=MailStatus.QUEUED if mail_configured() else MailStatus.SKIPPED,
        duplicate_key=key,
    )


def queue_mail(application: Application) -> None:
    if application.mail_status == MailStatus.QUEUED:
        async_task(SEND_MAIL_TASK, application.pk, task_name=f"{MAIL_TASK_NAME} № {application.pk}")


@transaction.atomic
def accept(cleaned: Cleaned) -> Accepted:
    key = duplicate_key(cleaned)
    existing = recent_duplicate(key)
    if existing:
        return Accepted(existing.pk, duplicate=True)
    application = create(cleaned, key)
    transaction.on_commit(lambda: queue_mail(application))
    return Accepted(application.pk, duplicate=False)


def purge_expired() -> str:
    cutoff = timezone.now() - timedelta(days=settings.APPLICATION_RETENTION_DAYS)
    removed, _ = Application.objects.filter(received_at__lt=cutoff).delete()
    return f"Удалено заявок старше {settings.APPLICATION_RETENTION_DAYS} дней: {removed}"
