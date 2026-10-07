from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from hashlib import sha256

from django.conf import settings
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from applications.consent import ADS_CONSENT_VERSION, CONSENT_VERSION
from applications.delivery import queue_mail
from applications.mail import skip_reason
from applications.models import CLOSED_STATUSES, Application, MailStatus, Status
from applications.parsing import Cleaned
from applications.topics import is_anonymous
from catalog.models import Program

NOT_STORED = ("program_id", "program_title", "ads_consent")


@dataclass(frozen=True)
class Accepted:
    id: int
    duplicate: bool


def duplicate_key(cleaned: Cleaned) -> str:
    if is_anonymous(cleaned.topic):
        return "|".join((cleaned.topic, sha256(cleaned.comment.encode()).hexdigest()))
    digits = "".join(char for char in cleaned.phone if char.isdigit())
    return "|".join((cleaned.topic, cleaned.email.lower(), digits, cleaned.program_id))


def recent_duplicate(key: str) -> Application | None:
    since = timezone.now() - timedelta(minutes=settings.APPLICATION_DUPLICATE_MINUTES)
    return Application.objects.filter(duplicate_key=key, received_at__gte=since).first()


def program_for(program_id: str) -> Program | None:
    return Program.objects.filter(hse_id=program_id).first() if program_id else None


def consent_fields(cleaned: Cleaned) -> dict[str, object]:
    if is_anonymous(cleaned.topic):
        return {}
    now = timezone.now()
    fields: dict[str, object] = {"consent_at": now, "consent_version": CONSENT_VERSION}
    if cleaned.ads_consent:
        fields |= {"ads_consent_at": now, "ads_consent_version": ADS_CONSENT_VERSION}
    return fields


def create(cleaned: Cleaned, key: str) -> Application:
    program = program_for(cleaned.program_id)
    reason = skip_reason(cleaned.topic)
    fields = {name: value for name, value in cleaned.__dict__.items() if name not in NOT_STORED}
    return Application.objects.create(
        **fields,
        **consent_fields(cleaned),
        program=program,
        program_title=program.title if program else cleaned.program_title,
        mail_status=MailStatus.SKIPPED if reason else MailStatus.QUEUED,
        mail_error=reason,
        duplicate_key=key,
    )


def queue_if_ready(application: Application) -> None:
    if application.mail_status == MailStatus.QUEUED:
        queue_mail(application.pk)


@dataclass(frozen=True)
class Resent:
    queued: int
    already_sent: int
    blocked: dict[str, int]


def blocked_by_reason(applications: list[Application]) -> dict[str, list[int]]:
    blocked: dict[str, list[int]] = {}
    for application in applications:
        reason = skip_reason(application.topic)
        if reason:
            blocked.setdefault(reason, []).append(application.pk)
    return blocked


def mark_blocked(blocked: dict[str, list[int]]) -> None:
    for reason, ids in blocked.items():
        Application.objects.filter(pk__in=ids).update(mail_status=MailStatus.SKIPPED, mail_error=reason)


def queue_again(ids: list[int]) -> None:
    Application.objects.filter(pk__in=ids).update(mail_status=MailStatus.QUEUED, mail_error="", mail_attempts=0)
    for application_id in ids:
        transaction.on_commit(partial(queue_mail, application_id))


@transaction.atomic
def resend(applications: list[Application]) -> Resent:
    unsent = [application for application in applications if application.mail_status != MailStatus.SENT]
    blocked = blocked_by_reason(unsent)
    held = {application_id for ids in blocked.values() for application_id in ids}
    ready = [application.pk for application in unsent if application.pk not in held]
    mark_blocked(blocked)
    queue_again(ready)
    return Resent(len(ready), len(applications) - len(unsent), {reason: len(ids) for reason, ids in blocked.items()})


def set_status(applications: QuerySet[Application], status: Status) -> int:
    if status not in CLOSED_STATUSES:
        return applications.update(status=status, closed_at=None)
    applications.filter(closed_at__isnull=True).update(closed_at=timezone.now())
    return applications.update(status=status)


@transaction.atomic
def accept(cleaned: Cleaned) -> Accepted:
    key = duplicate_key(cleaned)
    existing = recent_duplicate(key)
    if existing:
        return Accepted(existing.pk, duplicate=True)
    application = create(cleaned, key)
    transaction.on_commit(lambda: queue_if_ready(application))
    return Accepted(application.pk, duplicate=False)


def expired_applications() -> QuerySet[Application]:
    now = timezone.now()
    closed_before = now - timedelta(days=settings.APPLICATION_CLOSED_RETENTION_DAYS)
    received_before = now - timedelta(days=settings.APPLICATION_MAX_RETENTION_DAYS)
    return Application.objects.filter(Q(closed_at__lt=closed_before) | Q(received_at__lt=received_before))


def purge_expired() -> str:
    removed, _ = expired_applications().delete()
    return (
        f"Удалено заявок: {removed} (рассмотренные — через {settings.APPLICATION_CLOSED_RETENTION_DAYS} дн. "
        f"после итога, остальные — через {settings.APPLICATION_MAX_RETENTION_DAYS} дн. после получения)"
    )


def withdraw_ads_consent(applications: QuerySet[Application]) -> int:
    active = applications.filter(ads_consent_at__isnull=False, ads_consent_withdrawn_at__isnull=True)
    return active.update(ads_consent_withdrawn_at=timezone.now())
