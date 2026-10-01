import json
from pathlib import Path

import pytest

from catalog.slugs import FALLBACK_SLUG, MAX_SLUG_LENGTH, program_path, slugify

FIXTURES = Path(__file__).parent / "fixtures"
SEED = Path(__file__).parents[1] / "catalog" / "seed" / "catalog.json"


def test_paths_match_previous_site():
    expected = set(FIXTURES.joinpath("legacy_program_paths.txt").read_text().split())
    programs = json.loads(SEED.read_text())["programs"]
    assert {program_path(p["title"], str(p["id"])) for p in programs} == expected


@pytest.mark.parametrize(
    ("title", "slug"),
    [
        ("Английское контрактное право", "angliyskoe-kontraktnoe-pravo"),
        ("GR в фарме", "gr-v-farme"),
        ("!!!", FALLBACK_SLUG),
    ],
)
def test_slugify(title, slug):
    assert slugify(title) == slug


def test_slug_is_limited():
    assert len(slugify("очень длинное название " * 10)) <= MAX_SLUG_LENGTH
