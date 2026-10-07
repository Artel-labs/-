import re
from dataclasses import dataclass, field
from functools import partial
from typing import Any

from applications.models import ApplicantType, Topic
from applications.rules import EMAIL_TYPO, email_looks_valid, phone_problem
from applications.schemas import ApplicationIn
from applications.topics import TopicRule, rule_for

LIMITS = {
    "first_name": 80,
    "last_name": 80,
    "phone": 40,
    "email": 160,
    "company": 160,
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
    company: str
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


def line_if(keep: bool, value: Any, name: str) -> str:
    return line(value, name) if keep else ""


def paragraph(value: Any, name: str) -> str:
    if value is None:
        return ""
    text = EXTRA_BREAKS.sub("\n\n", INLINE_SPACES.sub(" ", LINE_BREAKS.sub("\n", str(value)))).strip()
    return text[: LIMITS[name]]


def flag(value: Any) -> bool:
    return value in TRUE_VALUES


def choice(value: Any, choices: type[Topic] | type[ApplicantType], default: str) -> str:
    return value if isinstance(value, str) and value in choices.values else default


MISSING = {
    "first_name": FieldError("firstName", "Укажите имя."),
    "last_name": FieldError("lastName", "Укажите фамилию."),
    "phone": FieldError("phone", "Укажите телефон."),
    "email": FieldError("email", "Укажите электронную почту."),
}


def format_error(name: str, value: str) -> FieldError | None:
    if name == "phone":
        problem = phone_problem(value)
        return FieldError("phone", problem) if problem else None
    if name == "email" and not email_looks_valid(value):
        return FieldError("email", EMAIL_TYPO)
    return None


def contact_errors(contacts: dict[str, str], required: frozenset[str]) -> list[FieldError]:
    errors = []
    for name, missing in MISSING.items():
        value = contacts[name]
        error = format_error(name, value) if value else missing if name in required else None
        if error:
            errors.append(error)
    return errors


def contacts_of(data: ApplicationIn) -> dict[str, str]:
    return {name: line(getattr(data, name), name) for name in MISSING}


def allowed_value(data: ApplicationIn, rule: TopicRule, name: str) -> Any:
    return getattr(data, name) if name in rule.allowed else None


def applicant_type_of(data: ApplicationIn, rule: TopicRule) -> str:
    if "applicant_type" not in rule.allowed:
        return ""
    return choice(data.applicant_type, ApplicantType, ApplicantType.PERSONAL)


def topic_fields(data: ApplicationIn, rule: TopicRule) -> dict[str, Any]:
    applicant_type = applicant_type_of(data, rule)
    corporate = applicant_type == ApplicantType.CORPORATE
    corporate_line = partial(line_if, corporate)
    return {
        "applicant_type": applicant_type,
        "employees_count": corporate_line(allowed_value(data, rule, "employees_count"), "employees_count"),
        "timeframe": corporate_line(allowed_value(data, rule, "timeframe"), "timeframe"),
        "company": line(allowed_value(data, rule, "company"), "company"),
        "program_id": line(allowed_value(data, rule, "program_id"), "program_id"),
        "program_title": line(allowed_value(data, rule, "program_title"), "program_title"),
    }


def parse(data: ApplicationIn) -> Parsed:
    topic = choice(data.topic, Topic, Topic.PROGRAM)
    rule = rule_for(topic)
    contacts = contacts_of(data)
    errors = contact_errors(contacts, rule.required)
    if not flag(data.consent):
        errors.append(FieldError("consent", "Без согласия на обработку персональных данных заявку принять нельзя."))
    if errors:
        return Parsed(errors=errors)
    return Parsed(
        Cleaned(
            topic=topic,
            **contacts,
            comment=paragraph(data.comment, "comment"),
            no_announcements=flag(data.no_announcements),
            **topic_fields(data, rule),
        )
    )
