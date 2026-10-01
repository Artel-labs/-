import json
from pathlib import Path
from typing import Any

from catalog.hse.details import ProgramDetails

FIXTURES = Path(__file__).parent / "fixtures" / "hse"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def expected(program_id: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(fixture(f"program-{program_id}.expected.json"))
    return data


def legacy_view(details: ProgramDetails) -> dict[str, Any]:
    notice = details.notice
    return {
        "tagline": details.tagline or None,
        "about": details.about or None,
        "audience": {"intro": details.audience_intro or None, "items": details.audience} if details.audience else None,
        "results": details.results or None,
        "modules": [{"title": m.title, "hours": m.hours or None, "topics": m.topics} for m in details.modules] or None,
        "teachers": [{"name": t.name, "about": t.about or None} for t in details.teachers] or None,
        "feedback": [{"text": r.text, "author": r.author} for r in details.reviews] or None,
        "hours": details.hours or None,
        "language": details.language or None,
        "schedule": details.schedule or None,
        "taxRefund": details.tax_refund or None,
        "discounts": details.discounts,
        "admissionDocs": details.admission_documents,
        "advantages": details.advantages,
        "files": [{"kind": f.kind, "title": f.title, "size": f.size or None, "url": f.url} for f in details.files],
        "notice": {"date": notice.date or None, "text": notice.text, "url": notice.url or None} if notice else None,
        "faq": [{"q": f.question, "a": f.answer} for f in details.faq],
        "ogImage": details.image_url or None,
        "teacherPhotos": [{"name": t.name, "src": t.photo_url} for t in details.teachers if t.photo_url],
    }


def normalized_legacy(data: dict[str, Any]) -> dict[str, Any]:
    notice = data.get("notice")
    if notice and notice.get("date") == "":
        data = {**data, "notice": {**notice, "date": None}}
    return data
