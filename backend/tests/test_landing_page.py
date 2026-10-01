import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from catalog.landing_schemas import LandingOut
from catalog.models import Program
from catalog.presentation.landing.page import landing_page

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_landing.json").read_text(encoding="utf-8"))
LEGACY_DAY = date(2026, 10, 1)
LEGACY_CATALOG = "Каталог программ.html"
LEGACY_IMAGES = "images/"
MEDIA_URL = "/media/"
STEP_COLORS = {
    1: "--step-bg:#1658DA;--step-ink:#FFFFFF;--step-soft:rgba(255,255,255,.86)",
    2: "--step-bg:#0B2A69;--step-ink:#FFFFFF;--step-soft:rgba(255,255,255,.86)",
    3: "--step-bg:#E6D4BF;--step-ink:#211E1B;--step-soft:#5A5248",
    4: "--step-bg:#CEDFFD;--step-ink:#211E1B;--step-soft:#48423A",
}


def site_href(href: str) -> str:
    if href.startswith(LEGACY_CATALOG):
        return "/catalog" + href.removeprefix(LEGACY_CATALOG)
    if href.startswith("programs/"):
        return f"/{href}"
    if href.startswith(LEGACY_IMAGES):
        return MEDIA_URL + href.removeprefix(LEGACY_IMAGES)
    return href


@pytest.fixture
def page(settings, tmp_path) -> LandingOut:
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())
    return landing_page(Program.objects.filter(is_published=True), LEGACY_DAY)


def legacy_links(pairs: list[list[str]]) -> list[list[str]]:
    return [[site_href(href), title] for href, title in pairs]


def test_menu_matches_previous_site(page):
    spheres = [
        {
            "href": sphere.href,
            "title": sphere.title,
            "count": sphere.count,
            "programs": [[link.href, link.title] for link in sphere.programs],
            "more": None if sphere.more is None else [sphere.more.href, sphere.more.title],
        }
        for sphere in page.menu.spheres
    ]
    legacy = [
        {
            **sphere,
            "href": site_href(sphere["href"]),
            "programs": legacy_links(sphere["programs"]),
            "more": None if sphere["more"] is None else [site_href(sphere["more"][0]), sphere["more"][1]],
        }
        for sphere in LEGACY["panel"]["spheres"]
    ]
    assert spheres == legacy
    assert f"Все {page.menu.total} программ с фильтрами" == LEGACY["panel"]["all"]


def test_sphere_cards_match_previous_site(page):
    cards = [card.dict() for card in page.spheres]
    assert cards == [{**card, "href": site_href(card["href"])} for card in LEGACY["spheres"]]


def format_record(row: Any) -> dict[str, Any]:
    doc = row.doc
    return {
        "doc": None if doc is None else [f"images/{doc.file}", doc.ext, str(doc.height), doc.name],
        "band": STEP_COLORS[row.step],
        "index": row.index,
        "title": row.title,
        "desc": row.desc,
        "facts": row.document,
        "stats": [[stat.key, stat.value] for stat in row.stats],
        "start": row.start,
        "count": row.count,
        "ctas": [[row.cta.href, row.cta.label, "_blank" if row.cta.external else "", row.cta.application]],
    }


def test_formats_match_previous_site(page):
    legacy = [{**row, "ctas": [[site_href(cta[0]), *cta[1:]] for cta in row["ctas"]]} for row in LEGACY["formats"]]
    assert [format_record(row) for row in page.formats] == legacy


def legacy_teacher(record: dict[str, Any]) -> dict[str, Any]:
    payload = record["payload"]
    programs = [{"t": item["t"], "h": site_href(item["h"])} for item in payload["programs"]]
    photo = record["photo"]
    return {
        **record,
        "payload": {**payload, "programs": programs},
        "photo": None if photo is None else [site_href(photo[0]), site_href(photo[1]), photo[2]],
    }


def teacher_record(card: Any) -> dict[str, Any]:
    photo = card.photo
    return {
        "payload": json.loads(card.payload),
        "initials": card.initials,
        "photo": None if photo is None else [photo.src, photo.webp, photo.alt],
        "name": card.name,
        "link": card.page,
        "more": [card.more_label, card.count],
        "desc": card.about,
    }


def test_teachers_match_previous_site(page):
    assert [teacher_record(card) for card in page.teachers] == [legacy_teacher(record) for record in LEGACY["teachers"]]


def test_starts_strip_matches_previous_site(page):
    starts = [[item.path, item.label, item.big, item.is_month, item.small, item.title] for item in page.starts]
    assert starts == [[site_href(item[0]), *item[1:]] for item in LEGACY["starts"]]


def test_reviews_match_previous_site(page):
    reviews = [[item.text, item.author, item.path, item.program] for item in page.reviews]
    assert reviews == [[text, author, site_href(href), title] for text, author, href, title in LEGACY["reviews"]]


def top_record(item: Any) -> dict[str, str]:
    record = {
        "image": item.image,
        "imageWebp": item.image_webp,
        "id": item.id,
        "start": item.start,
        "rank": item.rank,
        "title": item.title,
        "tagline": item.tagline,
        "kind": item.kind,
        "format": item.format,
        "formatTip": item.format_tip,
        "doc": item.doc,
        "docTip": item.doc_tip,
        "duration": item.duration,
        "price": item.price,
        "href": item.path,
    }
    return {key: value for key, value in record.items() if value or key not in ("image", "imageWebp")}


def test_top_programs_match_previous_site(page):
    legacy = [
        {key: site_href(value) if key in ("image", "imageWebp", "href") else value for key, value in item.items()}
        for item in LEGACY["top"]
    ]
    assert [top_record(item) for item in page.top] == legacy


def test_landing_endpoint(client, page):
    response = client.get("/api/catalog/landing")
    assert response.status_code == 200
    assert len(response.json()["teachers"]) == len(LEGACY["teachers"])
