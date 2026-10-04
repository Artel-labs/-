import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from catalog.models import Program
from catalog.presentation.tg import tg_catalog
from tests.typography import untypeset

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_tg.json").read_text(encoding="utf-8"))
LEGACY_DAY = date(2026, 10, 1)
RENAMED = {
    "start_label": "startLabel",
    "old_price": "oldPrice",
    "about_items": "aboutItems",
    "audience_intro": "audienceIntro",
    "price_terms": "priceTerms",
    "admission_docs": "admissionDocs",
}
LEGACY_PREFIXES = (("../images/", "/media/"), ("../files/", "/media/files/"))


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())


def local(value: Any) -> Any:
    if isinstance(value, str):
        for old, new in LEGACY_PREFIXES:
            if value.startswith(old):
                return new + value.removeprefix(old)
        return value
    if isinstance(value, list):
        return [local(item) for item in value]
    if isinstance(value, dict):
        return {key: local(item) for key, item in value.items()}
    return value


def current() -> dict[str, Any]:
    catalog = tg_catalog(Program.objects.filter(is_published=True), LEGACY_DAY).dict()
    programs = [{RENAMED.get(key, key): value for key, value in program.items()} for program in catalog["programs"]]
    return {"programs": programs, "spheres": catalog["spheres"]}


def test_spheres_match_previous_mini_app(seeded):
    assert untypeset(current()["spheres"]) == untypeset(LEGACY["spheres"])


def test_programs_match_previous_mini_app(seeded):
    programs = current()["programs"]
    assert [program["id"] for program in programs] == [program["id"] for program in LEGACY["programs"]]
    for mine, legacy in zip(programs, LEGACY["programs"], strict=True):
        assert untypeset(mine) == untypeset(local(legacy)), legacy["id"]


def test_endpoint_hides_unpublished(client, seeded):
    Program.objects.filter(hse_id="856421092").update(is_published=False)
    response = client.get("/api/catalog/tg")
    assert response.status_code == 200
    assert "856421092" not in [program["id"] for program in response.json()["programs"]]
