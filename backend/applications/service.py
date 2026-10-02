from dataclasses import dataclass
from datetime import timedelta
from functools import partial

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from applications.delivery import queue_mail
from applications.mail import skip_reason
from applications.models import Application, MailStatus
from applications.parsing import Cleaned
from catalog.models import Program


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
    reason = skip_reason(cleaned.topic)
    fields = {name: value for name, value in cleaned.__dict__.items() if name not in ("program_id", "program_title")}
    return Application.objects.create(
        **fields,
        program=program,
        program_title=program.title if program else cleaned.program_title,
        mail_status=MailStatus.SKIPPED if reason else MailStatus.QUEUED,
        mail_error=reason,
        duplicate_key=key,
    )


def queue_if_ready(application: Application) -> None:
    if application.mail_status == MailStatus.QUEUED:
        queue_mail(application.pk)


@transaction.atomic
def resend(applications: list[Application]) -> int:
    pending = [application.pk for application in applications if application.mail_status != MailStatus.SENT]
    Application.objects.filter(pk__in=pending).update(mail_status=MailStatus.QUEUED, mail_error="", mail_attempts=0)
    for application_id in pending:
        transaction.on_commit(partial(queue_mail, application_id))
    return len(pending)


@transaction.atomic
def accept(cleaned: Cleaned) -> Accepted:
    key = duplicate_key(cleaned)
    existing = recent_duplicate(key)
    if existing:
        return Accepted(existing.pk, duplicate=True)
    application = create(cleaned, key)
    transaction.on_commit(lambda: queue_if_ready(application))
    return Accepted(application.pk, duplicate=False)


def purge_expired() -> str:
    cutoff = timezone.now() - timedelta(days=settings.APPLICATION_RETENTION_DAYS)
    removed, _ = Application.objects.filter(received_at__lt=cutoff).delete()
    return f"Удалено заявок старше {settings.APPLICATION_RETENTION_DAYS} дней: {removed}"
