from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from applications.models import Application, MailStatus
from applications.recipients import all_recipients

NOT_SET = "не задан"
NO_ENCRYPTION_SET = "не задано"
ENV_KEYS = "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS"
NOT_CONFIGURED = f"Почтовый сервер не настроен. Заполните в файле .env на сервере: {ENV_KEYS} — и перезапустите сайт."
PROBLEM_STATUSES = (MailStatus.FAILED, MailStatus.SKIPPED)
SSL = "SSL (шифрование сразу)"
STARTTLS = "STARTTLS"
PLAIN = "без шифрования"
NO_SERVER = "Почта не настроена — письма по заявкам не уходят."
NO_RECIPIENTS = "Письма по заявкам не уходят: нет активных получателей. Добавьте их в «Заявки» → «Получатели писем»."
LAST_FAILED = "Последнее письмо по заявке не ушло — подробности ниже."
READY = "Почта настроена."


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
    ok: bool
    headline: str


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


def failed_last(sent: Event | None, problem: Event | None) -> bool:
    return problem is not None and (sent is None or problem.application_id > sent.application_id)


def headline(configured: bool, sent: Event | None, problem: Event | None) -> tuple[bool, str]:
    if not configured:
        return False, NO_SERVER
    if not all_recipients():
        return False, NO_RECIPIENTS
    if failed_last(sent, problem):
        return False, LAST_FAILED
    return True, READY


def mail_state() -> MailState:
    configured = bool(settings.EMAIL_HOST)
    sent, problem = last_sent(), last_problem()
    ok, text = headline(configured, sent, problem)
    return MailState(configured, server_rows(), sent, problem, ok, text)
