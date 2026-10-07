from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from django.core.files import File
from django.db import transaction

from catalog.models import FaqItem, Module, Program, ProgramFile, ProgramTeacher, Review, Source, Teacher
from catalog.spheres import ensure_spheres, match_sphere
from catalog.teachers import canonical_name
from catalog.top_picks import pin_high_rating
from catalog.typesetting import typeset_program

MOSCOW = ZoneInfo("Europe/Moscow")
MILLISECONDS = 1000

Record = dict[str, Any]


def lines(items: list[str] | None) -> str:
    return "\n".join(" ".join(item.split()) for item in items or [])


def start_date(timestamp: int | None) -> date | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp / MILLISECONDS, MOSCOW).date()


def attach(field: Any, root: Path, relative: str | None) -> None:
    if not relative:
        return
    path = root / relative
    with path.open("rb") as handle:
        field.save(path.name, File(handle), save=False)


def import_teachers(data: Record, root: Path) -> dict[str, Teacher]:
    names = set(data.get("teacherPhotos") or {}) | set(data.get("teacherPages") or {})
    names |= {canonical_name(t["name"]) for p in data["programs"] for t in p.get("teachers") or []}
    teachers = {}
    for name in sorted(names):
        teacher = Teacher(
            name=name,
            page_url=(data.get("teacherPages") or {}).get(name, ""),
            show_on_landing=name not in (data.get("teachersHiddenOnLanding") or []),
        )
        attach(teacher.photo, root, (data.get("teacherPhotos") or {}).get(name))
        teacher.save()
        teachers[name] = teacher
    return teachers


def program_fields(record: Record) -> Record:
    audience = record.get("audience") or {}
    notice = record.get("notice") or {}
    return {
        "hse_id": str(record["id"]),
        "title": record["title"],
        "hse_url": record.get("url") or "",
        "type_short": record["type"]["shortTitle"],
        "type_title": record["type"]["title"],
        "study_format": record["studyFormat"]["title"],
        "duration": record.get("duration") or "",
        "hours": record.get("hours") or "",
        "language": record.get("language") or "",
        "schedule": record.get("schedule") or "",
        "start_date": start_date(record.get("startDate")),
        "start_month_only": bool(record.get("isStartDateWithoutDay")),
        "price": record.get("discountPrice"),
        "base_price": record.get("educationPricing"),
        "tax_refund": record.get("taxRefund") or "",
        "tagline": record.get("tagline") or "",
        "about": record.get("about") or "",
        "audience_intro": audience.get("intro") or "",
        "audience": lines(audience.get("items")),
        "results": lines(record.get("results")),
        "advantages": lines(record.get("advantages")),
        "discounts": lines(record.get("discounts")),
        "admission_documents": lines(record.get("admissionDocs")),
        "notice_date": notice.get("date") or "",
        "notice_text": notice.get("text") or "",
        "notice_url": notice.get("url") or "",
        "source": record.get("source") or Source.HSE,
        "locked": bool(record.get("locked")),
    }


def place_in_sphere(program: Program, spheres: dict[str, Any]) -> None:
    match = match_sphere(program.title)
    if match:
        program.sphere = spheres[match.slug]
        program.position = match.position


def import_modules(program: Program, record: Record) -> None:
    for position, module in enumerate(record.get("modules") or []):
        Module.objects.create(
            program=program,
            title=module["title"],
            hours=module.get("hours") or "",
            topics=lines(module.get("topics")),
            position=position,
        )


def import_faq(program: Program, record: Record) -> None:
    for position, item in enumerate(record.get("faq") or []):
        FaqItem.objects.create(program=program, question=item["q"], answer=item["a"], position=position)


def import_reviews(program: Program, record: Record) -> None:
    for position, item in enumerate(record.get("feedback") or []):
        Review.objects.create(program=program, text=item["text"], author=item.get("author") or "", position=position)


def import_files(program: Program, record: Record, root: Path) -> None:
    for position, item in enumerate(record.get("files") or []):
        document = ProgramFile(
            program=program,
            kind=item["kind"],
            title=item["title"],
            size_label=item.get("size") or "",
            source_url=item.get("url") or "",
            position=position,
        )
        attach(document.file, root, item.get("path"))
        document.save()


def import_program_teachers(program: Program, record: Record, teachers: dict[str, Teacher]) -> None:
    for position, item in enumerate(record.get("teachers") or []):
        teacher = teachers[canonical_name(item["name"])]
        ProgramTeacher.objects.create(
            program=program, teacher=teacher, about=item.get("about") or "", position=position
        )


def import_program(
    record: Record, root: Path, spheres: dict[str, Any], teachers: dict[str, Teacher], catalog_position: int
) -> Program:
    program = Program(**program_fields(record), catalog_position=catalog_position)
    place_in_sphere(program, spheres)
    attach(program.image, root, record.get("image"))
    program.save()
    import_modules(program, record)
    import_faq(program, record)
    import_reviews(program, record)
    import_files(program, record, root)
    import_program_teachers(program, record, teachers)
    typeset_program(program)
    return program


@transaction.atomic
def import_catalog(data: Record, root: Path) -> int:
    spheres = ensure_spheres()
    teachers = import_teachers(data, root)
    for catalog_position, record in enumerate(data["programs"]):
        import_program(record, root, spheres, teachers, catalog_position)
    pin_high_rating(Program.objects)
    return len(data["programs"])
