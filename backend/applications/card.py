from dataclasses import dataclass

from django.urls import reverse

from applications.mail import applicant_field, source_labels
from applications.models import ApplicantType, Application, MailStatus, Status


@dataclass(frozen=True)
class Fact:
    title: str
    value: str


@dataclass(frozen=True)
class Card:
    facts: list[Fact]
    statuses: list[tuple[str, str]]
    status_url: str
    resend_url: str
    program_url: str
    mail_sent: bool


def announcements(application: Application) -> str:
    return "не присылать" if application.no_announcements else "согласен получать"


def facts(application: Application) -> list[Fact]:
    corporate = application.applicant_type == ApplicantType.CORPORATE
    candidates = [
        Fact(applicant_field(), application.get_applicant_type_display() if corporate else ""),
        Fact("Сотрудников к обучению", application.employees_count),
        Fact("Желаемые сроки", application.timeframe),
        Fact("Должность", application.position),
        Fact("Место работы", application.company),
        Fact("Откуда узнали", ", ".join(source_labels(application))),
        Fact("Анонсы новых программ", announcements(application)),
    ]
    return [fact for fact in candidates if fact.value]


def admin_url(name: str, application: Application) -> str:
    return reverse(f"admin:applications_application_{name}", args=[application.pk])


def card_of(application: Application) -> Card:
    return Card(
        facts=facts(application),
        statuses=list(Status.choices),
        status_url=admin_url("status", application),
        resend_url=admin_url("resend", application),
        program_url=f"/{application.program.path}" if application.program else "",
        mail_sent=application.mail_status == MailStatus.SENT,
    )
