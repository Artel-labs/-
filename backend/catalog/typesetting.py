from typing import Any

from catalog.typography import typeset

TYPESET_FIELDS: dict[str, tuple[str, ...]] = {
    "Program": (
        "title",
        "duration",
        "hours",
        "language",
        "schedule",
        "tax_refund",
        "tagline",
        "about",
        "audience_intro",
        "audience",
        "results",
        "advantages",
        "discounts",
        "admission_documents",
        "notice_text",
    ),
    "Module": ("title", "hours", "topics"),
    "FaqItem": ("question", "answer"),
    "Review": ("text", "author"),
    "ProgramFile": ("title",),
    "ProgramTeacher": ("about",),
}
RELATED = ("modules", "faq", "reviews", "files", "program_teachers")


def typeset_record(record: Any) -> None:
    changed = []
    for name in TYPESET_FIELDS[type(record).__name__]:
        value = getattr(record, name)
        fresh = typeset(value)
        if fresh != value:
            setattr(record, name, fresh)
            changed.append(name)
    if changed:
        record.save(update_fields=changed)


def typeset_program(program: Any) -> None:
    typeset_record(program)
    for relation in RELATED:
        for item in getattr(program, relation).all():
            typeset_record(item)
