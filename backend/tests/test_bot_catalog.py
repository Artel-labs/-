import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from catalog.models import Program
from catalog.presentation.bot import bot_catalog

pytestmark = pytest.mark.django_db

FIXTURE = Path(__file__).parent / "fixtures" / "legacy_bot_catalog.json"
LEGACY = json.loads(FIXTURE.read_text(encoding="utf-8"))["programs"]
LEGACY_DAY = date(2026, 10, 1)
RENAMED = {"format_label": "formatLabel", "price_label": "priceLabel", "start_iso": "startIso"}


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())


def legacy_record(record: dict[str, Any]) -> dict[str, Any]:
    return {**record, "url": f"/{record['url']}"}


def current_records() -> dict[str, dict[str, Any]]:
    programs = bot_catalog(Program.objects.filter(is_published=True), LEGACY_DAY)
    records = [{RENAMED.get(key, key): value for key, value in program.dict().items()} for program in programs]
    return {record["id"]: record for record in records}


def test_bot_catalog_matches_previous_site(seeded):
    current = current_records()
    assert list(current) == [record["id"] for record in LEGACY]
    for record in LEGACY:
        assert current[record["id"]] == legacy_record(record), record["id"]


def test_bot_catalog_endpoint_hides_unpublished(client, seeded):
    Program.objects.filter(hse_id="856421092").update(is_published=False)
    response = client.get("/api/catalog/bot")
    assert response.status_code == 200
    ids = [program["id"] for program in response.json()]
    assert "856421092" not in ids
    assert len(ids) == len(LEGACY) - 1
