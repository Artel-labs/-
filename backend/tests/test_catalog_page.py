import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from catalog.models import Program, Source
from catalog.presentation.catalog import catalog_page
from catalog.presentation.timeline import DAY_PX
from catalog.schemas import CardOut, CatalogPageOut, StartsOut
from tests.typography import untypeset

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_catalog.json").read_text(encoding="utf-8"))
LEGACY_DAY = date(2026, 10, 1)
LEGACY_AXIS_START = date(2026, 10, 1)
SAME_AS_LEGACY = ("width", "chips", "months", "today", "items")
LEGACY_SITE = "https://example.com"
LEGACY_IMAGES = "images/"
MEDIA_URL = "/media/"


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.SITE_URL = LEGACY_SITE
    call_command("seed_catalog", stdout=StringIO())


@pytest.fixture
def page(seeded) -> CatalogPageOut:
    return catalog_page(Program.objects.filter(is_published=True), LEGACY_DAY)


def card_record(card: CardOut) -> dict[str, Any]:
    compare = card.compare
    return {
        "data": {
            "data-type": card.type_short,
            "data-format": card.format,
            "data-sphere": card.sphere,
            "data-duration": card.duration,
            "data-price": str(card.price_sort),
            "data-start": str(card.start_sort),
            "data-title": card.title_sort,
            "data-search": card.search,
            "data-id": card.hse_id,
            "data-cmp-format": compare.format,
            "data-cmp-duration": compare.duration,
            "data-cmp-start": compare.start,
            "data-cmp-modules": compare.modules,
            "data-cmp-teachers": str(compare.teachers),
            "data-cmp-audience": compare.audience,
        },
        "compare_label": f"Сравнить: {card.title}",
        "href": card.path,
        "thumb": None if card.thumb is None else [card.thumb.src, card.thumb.webp, card.thumb.alt],
        "sphere": card.sphere_title,
        "title": card.title,
        "tags": [[tag.kind, tag.text, tag.tip] for tag in card.tags],
        "meta": card.start,
        "price": card.price,
        "apply": [card.hse_id, card.title, card.path, f"Заявка: {card.title}"],
    }


def legacy_card(record: dict[str, Any]) -> dict[str, Any]:
    thumb = record["thumb"]
    if thumb:
        thumb = [path.replace(LEGACY_IMAGES, MEDIA_URL, 1) for path in thumb[:2]] + [thumb[2]]
    return {**record, "thumb": thumb}


def starts_record(starts: StartsOut) -> dict[str, Any]:
    return {
        "width": starts.width,
        "chips": [
            [month.label, str(month.count), month.scroll, "true" if index == 0 else "false"]
            for index, month in enumerate(starts.months)
        ],
        "months": [[month.left, month.width, month.label, str(month.count)] for month in starts.months],
        "ticks": [[tick.left, tick.kind] for tick in starts.ticks],
        "today": starts.today,
        "items": [
            [
                item.lane,
                item.left,
                item.pin,
                item.path,
                item.hint,
                item.when,
                item.title,
                item.sphere,
                item.meta,
                item.price,
            ]
            for item in starts.items
        ],
    }


def test_cards_match_previous_site(page):
    assert untypeset([card_record(card) for card in page.cards]) == untypeset(
        [legacy_card(record) for record in LEGACY["cards"]]
    )


def test_filters_match_previous_site(page):
    chips = {
        group: [[chip.label, chip.value, chip.active] for chip in getattr(page.filters, group)]
        for group in LEGACY["filters"]
    }
    assert untypeset(chips) == untypeset(LEGACY["filters"])


def test_starts_board_matches_previous_site(page):
    assert page.starts is not None
    record, legacy = starts_record(page.starts), LEGACY["starts"]
    assert untypeset({key: record[key] for key in SAME_AS_LEGACY}) == untypeset(
        {key: legacy[key] for key in SAME_AS_LEGACY}
    )


def test_starts_ticks_mark_mondays_and_month_starts(page):
    assert page.starts is not None
    legacy_lefts = {left for left, _ in LEGACY["starts"]["ticks"]}
    assert page.starts.ticks
    for tick in page.starts.ticks:
        day = date.fromordinal(LEGACY_AXIS_START.toordinal() + (tick.left - DAY_PX // 2) // DAY_PX)
        assert float(tick.left) in legacy_lefts
        assert tick.kind == ("is-month" if day.day == 1 else "is-week")
        assert day.day == 1 or day.weekday() == 0


def test_starts_months_have_captions(page):
    assert page.starts is not None
    assert [month.caption for month in page.starts.months] == ["Октябрь · 10 стартов", "Ноябрь · 12 стартов"]


def test_starts_legend_lists_spheres_on_board(page):
    assert page.starts is not None
    shown = {item.sphere for item in page.starts.items if item.sphere}
    slugs = [sphere.slug for sphere in page.starts.legend]
    assert set(slugs) == shown
    assert len(slugs) == len(set(slugs))
    assert all(sphere.title for sphere in page.starts.legend)


def test_structured_data_matches_previous_site(page):
    assert untypeset(json.loads(page.structured_data)) == untypeset(LEGACY["structured_data"])


def test_manual_programs_follow_hse_order(seeded):
    Program.objects.filter(hse_id="816497962").update(source=Source.MANUAL)
    page = catalog_page(Program.objects.all(), LEGACY_DAY)
    assert page.cards[-1].hse_id == "816497962"


def test_no_upcoming_starts_hides_board(seeded):
    assert catalog_page(Program.objects.all(), date(2030, 1, 1)).starts is None


def test_catalog_endpoint_lists_published_programs(client, seeded):
    Program.objects.filter(hse_id="856421092").update(is_published=False)
    response = client.get("/api/catalog/programs")
    assert response.status_code == 200
    assert "856421092" not in [card["hse_id"] for card in response.json()["cards"]]
    assert response.json()["total"] == len(LEGACY["cards"]) - 1


def test_card_tips_follow_brandbook_typography(page):
    tips = {tag.tip for card in page.cards for tag in card.tags if tag.tip}
    assert "Повышение квалификации. Итоговый документ — удостоверение о повышении квалификации НИУ ВШЭ." in tips
    assert not [tip for tip in tips if " – " in tip or " - " in tip]
