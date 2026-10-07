from dataclasses import dataclass

from django.urls import reverse

from applications.mail import ANONYMOUS_LINE, applicant_field, company_field, consent_state
from applications.models import ApplicantType, Application, MailStatus, Status
from applications.topics import is_anonymous


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
    anonymous_note: str


def announcements(application: Application) -> str:
    if is_anonymous(application.topic):
        return ""
    return "не присылать" if application.no_announcements else "согласен получать"


def facts(application: Application) -> list[Fact]:
    corporate = application.applicant_type == ApplicantType.CORPORATE
    candidates = [
        Fact(applicant_field(), application.get_applicant_type_display() if corporate else ""),
        Fact("Сотрудников к обучению", application.employees_count),
        Fact("Желаемые сроки", application.timeframe),
        Fact(company_field(), application.company),
        Fact("Анонсы новых программ", announcements(application)),
        Fact("Согласие на обработку ПДн", "" if is_anonymous(application.topic) else consent_state(application)),
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
        anonymous_note=ANONYMOUS_LINE if is_anonymous(application.topic) else "",
    )
