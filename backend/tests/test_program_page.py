import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from catalog.models import Program
from catalog.presentation.page import program_page
from catalog.schemas import ProgramPageOut
from tests.typography import untypeset

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_program_pages.json").read_text(encoding="utf-8"))
LEGACY_DAY = date(2026, 10, 1)
LEGACY_SITE = "https://example.com"


def plain(text: str) -> str:
    return " ".join(text.split())


@pytest.fixture
def pages(settings, tmp_path, django_db_blocker):
    settings.MEDIA_ROOT = tmp_path
    settings.SITE_URL = LEGACY_SITE
    call_command("seed_catalog", stdout=StringIO())
    return {program.hse_id: program_page(program, LEGACY_DAY) for program in Program.objects.select_related("sphere")}


def credential_fields(page: ProgramPageOut) -> list[str] | None:
    found = page.credential
    return None if found is None else [found.tag, found.name, found.note]


def comparable(page: ProgramPageOut) -> dict[str, Any]:
    about = page.about
    return {
        "page_title": page.page_title,
        "description": page.description,
        "canonical": page.canonical_url,
        "structured_data": page.structured_data,
        "crumb": page.crumb,
        "chips": page.chips,
        "price": plain(page.price),
        "price_terms": [plain(term) for term in page.price_terms],
        "facts": [[fact.label, plain(fact.value)] for fact in page.facts],
        "about": None if about is None else {"lead": about.lead, "body": about.body, "items": about.items},
        "audience": None if page.audience is None else {"intro": page.audience.intro, "items": page.audience.items},
        "results": page.results,
        "advantages": page.advantages,
        "modules": [{"title": m.title, "hours": m.hours, "topics": m.topics} for m in page.modules],
        "modules_label": page.modules_label if page.modules else "",
        "files": [[document.label, document.size] for document in page.files],
        "teachers_heading": page.teachers_heading if page.teachers else "",
        "teachers": [{"name": t.name, "about": t.about, "page_url": t.page_url} for t in page.teachers],
        "reviews": [[review.text, review.author] for review in page.reviews],
        "admission_documents": page.admission_documents,
        "faq": [[item.question, item.answer] for item in page.faq],
        "siblings": None
        if page.siblings is None
        else {
            "heading": f"Другие программы направления «{page.siblings.sphere_title}»",
            "count_label": f"{page.siblings.count_label} в направлении",
            "paths": [item.path.removeprefix("programs/") for item in page.siblings.items],
            "titles": [item.title for item in page.siblings.items],
        },
        "notice": None
        if page.notice is None
        else {
            "date": page.notice.date,
            "text": page.notice.text,
            "link": f"Смотреть на {page.notice.host}" if page.notice.url else "",
        },
        "pay_url": page.pay_url,
        "credential": credential_fields(page),
    }


def without_developer_placeholders(record: dict[str, Any]) -> dict[str, Any]:
    about = record["about"]
    if about and not (about["lead"] or about["body"] or about["items"]):
        record = {**record, "about": None}
    if not record["teachers"]:
        record = {**record, "teachers_heading": ""}
    return record


def normalized_legacy(record: dict[str, Any]) -> dict[str, Any]:
    record = {**record, "facts": [[label, plain(value)] for label, value in record["facts"]]}
    return without_developer_placeholders(record)


def test_program_pages_match_previous_site(pages):
    mismatched = {
        hse_id: field
        for hse_id, record in LEGACY.items()
        for field, value in normalized_legacy(record).items()
        if untypeset(comparable(pages[hse_id])[field]) != untypeset(value)
    }
    assert mismatched == {}
    assert len(pages) == len(LEGACY)


def test_page_has_cover_variants(pages):
    cover = pages["856421092"].cover
    assert cover is not None
    assert cover.src.endswith("programs/thumbs/856421092.jpg")
    assert cover.width == 640


def test_unpublished_program_is_not_served(client, pages):
    Program.objects.filter(hse_id="856421092").update(is_published=False)
    assert client.get("/api/catalog/programs/856421092").status_code == 404


def test_program_endpoint_returns_page(client, pages):
    response = client.get("/api/catalog/programs/856421092")
    assert response.status_code == 200
    assert response.json()["title"] == "Английское контрактное право"
