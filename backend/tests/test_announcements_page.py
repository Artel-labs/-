import json
from datetime import date
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from catalog.models import Program
from catalog.presentation.announcements import announcements_page
from catalog.schemas import AnnouncementsPageOut, StartOut, StartsOut
from tests.typography import untypeset

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_catalog.json").read_text(encoding="utf-8"))
LEGACY_DAY = date(2026, 10, 1)
LEGACY_SITE = "https://example.com"
FAR_FUTURE = date(2030, 1, 1)
OK = 200


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.SITE_URL = LEGACY_SITE
    call_command("seed_catalog", stdout=StringIO())


@pytest.fixture
def board(seeded) -> StartsOut:
    starts = announcements_page(Program.objects.filter(is_published=True), LEGACY_DAY).starts
    assert starts is not None
    return starts


def start_items(starts: StartsOut) -> list[StartOut]:
    return [item for month in starts.months for item in month.items]


def test_page_has_its_own_canonical_address(seeded):
    page: AnnouncementsPageOut = announcements_page(Program.objects.all(), LEGACY_DAY)
    assert page.canonical_url == f"{LEGACY_SITE}/announcements"


def test_starts_keep_previous_site_cards_in_date_order(board):
    cards = [
        [item.path, item.hint, item.when, item.title, item.sphere, item.meta, item.price] for item in start_items(board)
    ]
    assert untypeset(cards) == untypeset([item[3:] for item in LEGACY["starts"]["items"]])


def test_starts_are_grouped_by_month_with_anchors(board):
    months = [(month.anchor, month.label, month.caption, len(month.items)) for month in board.months]
    assert months == [
        ("starts-2026-10", "Октябрь", "Октябрь · 10 стартов", 10),
        ("starts-2026-11", "Ноябрь", "Ноябрь · 12 стартов", 12),
    ]


def test_starts_legend_lists_spheres_on_board(board):
    shown = {item.sphere for item in start_items(board) if item.sphere}
    slugs = [sphere.slug for sphere in board.legend]
    assert set(slugs) == shown
    assert len(slugs) == len(set(slugs))
    assert all(sphere.title for sphere in board.legend)


def test_no_upcoming_starts_leaves_board_empty(seeded):
    assert announcements_page(Program.objects.all(), FAR_FUTURE).starts is None


def test_announcements_endpoint_skips_hidden_programs(client, board):
    hidden = start_items(board)[0]
    Program.objects.filter(title=hidden.title).update(is_published=False)
    response = client.get("/api/catalog/announcements")
    assert response.status_code == OK
    titles = [item["title"] for month in response.json()["starts"]["months"] for item in month["items"]]
    assert hidden.title not in titles
