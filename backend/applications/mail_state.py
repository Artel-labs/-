from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from applications.models import Application, MailStatus

NOT_SET = "не задан"
NO_ENCRYPTION_SET = "не задано"
ENV_KEYS = "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS"
NOT_CONFIGURED = f"Почтовый сервер не настроен. Заполните в файле .env на сервере: {ENV_KEYS} — и перезапустите сайт."
PROBLEM_STATUSES = (MailStatus.FAILED, MailStatus.SKIPPED)
SSL = "SSL (шифрование сразу)"
STARTTLS = "STARTTLS"
PLAIN = "без шифрования"


@dataclass(frozen=True)
class Row:
    title: str
    value: str


@dataclass(frozen=True)
class Event:
    when: str
    text: str
    application_id: int


@dataclass(frozen=True)
class MailState:
    configured: bool
    rows: list[Row]
    last_sent: Event | None
    last_problem: Event | None


def encryption() -> str:
    if not settings.EMAIL_HOST:
        return NO_ENCRYPTION_SET
    if settings.EMAIL_USE_SSL:
        return SSL
    return STARTTLS if settings.EMAIL_USE_TLS else PLAIN


def server_rows() -> list[Row]:
    return [
        Row("Сервер", f"{settings.EMAIL_HOST}:{settings.EMAIL_PORT}" if settings.EMAIL_HOST else NOT_SET),
        Row("Шифрование", encryption()),
        Row("Логин", settings.EMAIL_HOST_USER or NOT_SET),
        Row("Пароль", "задан" if settings.EMAIL_HOST_PASSWORD else NOT_SET),
        Row("Отправитель", settings.DEFAULT_FROM_EMAIL or NOT_SET),
    ]


def moscow(application: Application) -> str:
    return timezone.localtime(application.received_at).strftime("%d.%m.%Y %H:%M")


def event(application: Application | None, text: str) -> Event | None:
    if application is None:
        return None
    return Event(moscow(application), text or application.get_mail_status_display(), application.pk)


def last_sent() -> Event | None:
    return event(Application.objects.filter(mail_status=MailStatus.SENT).first(), "")


def last_problem() -> Event | None:
    application = Application.objects.filter(mail_status__in=PROBLEM_STATUSES).first()
    return event(application, application.mail_error if application else "")


def mail_state() -> MailState:
    return MailState(bool(settings.EMAIL_HOST), server_rows(), last_sent(), last_problem())
