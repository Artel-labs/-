import re
from dataclasses import dataclass, field
from typing import Any

from applications.models import ApplicantType, Source, Topic
from applications.rules import EMAIL_TYPO, email_looks_valid, phone_problem
from applications.schemas import ApplicationIn

LIMITS = {
    "first_name": 80,
    "last_name": 80,
    "phone": 40,
    "email": 160,
    "position": 120,
    "company": 160,
    "source_other": 200,
    "comment": 1000,
    "program_id": 40,
    "program_title": 300,
    "employees_count": 40,
    "timeframe": 200,
}
TRUE_VALUES = (True, "true", "on", 1, "1")
LINE_BREAKS = re.compile(r"\r\n?")
INLINE_SPACES = re.compile(r"[ \t]+")
EXTRA_BREAKS = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


@dataclass
class Cleaned:
    topic: str
    applicant_type: str
    employees_count: str
    timeframe: str
    first_name: str
    last_name: str
    phone: str
    email: str
    position: str
    company: str
    sources: list[str]
    source_other: str
    comment: str
    no_announcements: bool
    program_id: str
    program_title: str


@dataclass
class Parsed:
    cleaned: Cleaned | None = None
    errors: list[FieldError] = field(default_factory=list)


def line(value: Any, name: str) -> str:
    text = " ".join(str(value).split()) if value is not None else ""
    return text[: LIMITS[name]]


def paragraph(value: Any, name: str) -> str:
    if value is None:
        return ""
    text = EXTRA_BREAKS.sub("\n\n", INLINE_SPACES.sub(" ", LINE_BREAKS.sub("\n", str(value)))).strip()
    return text[: LIMITS[name]]


def flag(value: Any) -> bool:
    return value in TRUE_VALUES


def choice(value: Any, choices: type[Topic] | type[ApplicantType], default: str) -> str:
    return value if isinstance(value, str) and value in choices.values else default


def sources(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    known = [str(item) for item in value if str(item) in Source.values]
    return list(dict.fromkeys(known))


def contact_errors(first_name: str, last_name: str, phone: str, email: str) -> list[FieldError]:
    errors = []
    if not first_name:
        errors.append(FieldError("firstName", "Укажите имя."))
    if not last_name:
        errors.append(FieldError("lastName", "Укажите фамилию."))
    problem = phone_problem(phone) if phone else "Укажите телефон."
    if problem:
        errors.append(FieldError("phone", problem))
    if not email:
        errors.append(FieldError("email", "Укажите электронную почту."))
    elif not email_looks_valid(email):
        errors.append(FieldError("email", EMAIL_TYPO))
    return errors


def parse(data: ApplicationIn) -> Parsed:
    first_name, last_name = line(data.first_name, "first_name"), line(data.last_name, "last_name")
    phone, email = line(data.phone, "phone"), line(data.email, "email")
    errors = contact_errors(first_name, last_name, phone, email)
    if not flag(data.consent):
        errors.append(FieldError("consent", "Без согласия на обработку персональных данных заявку принять нельзя."))
    if errors:
        return Parsed(errors=errors)
    chosen_sources = sources(data.sources)
    applicant_type = choice(data.applicant_type, ApplicantType, ApplicantType.PERSONAL)
    corporate = applicant_type == ApplicantType.CORPORATE
    return Parsed(
        Cleaned(
            topic=choice(data.topic, Topic, Topic.PROGRAM),
            applicant_type=applicant_type,
            employees_count=line(data.employees_count, "employees_count") if corporate else "",
            timeframe=line(data.timeframe, "timeframe") if corporate else "",
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            position=line(data.position, "position"),
            company=line(data.company, "company"),
            sources=chosen_sources,
            source_other=line(data.source_other, "source_other") if Source.OTHER in chosen_sources else "",
            comment=paragraph(data.comment, "comment"),
            no_announcements=flag(data.no_announcements),
            program_id=line(data.program_id, "program_id"),
            program_title=line(data.program_title, "program_title"),
        )
    )
