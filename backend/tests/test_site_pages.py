import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from catalog.models import Program

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_sitemap.json").read_text(encoding="utf-8"))
LEGACY_SITE = "https://example.com"
STATIC_PAGES = 4


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.SITE_URL = LEGACY_SITE
    call_command("seed_catalog", stdout=StringIO())


def sitemap(client) -> list[dict[str, str]]:
    response = client.get("/api/catalog/sitemap")
    assert response.status_code == 200
    entries: list[dict[str, str]] = response.json()
    return entries


def test_sitemap_lists_static_pages_first(client, seeded):
    assert sitemap(client)[:STATIC_PAGES] == LEGACY[:STATIC_PAGES]


def test_sitemap_matches_previous_site(client, seeded):
    entries = sitemap(client)
    assert sorted(entries, key=lambda item: item["loc"]) == sorted(LEGACY, key=lambda item: item["loc"])


def test_sitemap_skips_hidden_programs(client, seeded):
    hidden = Program.objects.get(hse_id="856421092")
    hidden.is_published = False
    hidden.save()
    locs = [entry["loc"] for entry in sitemap(client)]
    assert f"{LEGACY_SITE}/{hidden.path}" not in locs
    assert len(locs) == len(LEGACY) - 1


def test_site_endpoint_reports_public_urls(client, settings):
    settings.SITE_URL = LEGACY_SITE
    response = client.get("/api/site")
    assert response.status_code == 200
    assert response.json() == {"site_url": LEGACY_SITE, "image_url": f"{LEGACY_SITE}/images/hero-composite.jpg"}
