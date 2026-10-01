from typing import Any

from ninja import Field, Schema


class ApplicationIn(Schema):
    topic: Any = None
    applicant_type: Any = Field(None, alias="applicantType")
    employees_count: Any = Field(None, alias="employeesCount")
    timeframe: Any = None
    first_name: Any = Field(None, alias="firstName")
    last_name: Any = Field(None, alias="lastName")
    phone: Any = None
    email: Any = None
    position: Any = None
    company: Any = None
    sources: Any = None
    source_other: Any = Field(None, alias="sourceOther")
    comment: Any = None
    no_announcements: Any = Field(None, alias="noAnnouncements")
    consent: Any = None
    website: Any = None
    program_id: Any = Field(None, alias="programId")
    program_title: Any = Field(None, alias="programTitle")


class FieldErrorOut(Schema):
    field: str
    message: str


class AcceptedOut(Schema):
    ok: bool
    id: int | None = None


class RejectedOut(Schema):
    error: str
    fields: list[FieldErrorOut] = []
