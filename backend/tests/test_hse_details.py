import pytest

from catalog.hse.details import parse_details
from tests.hse_helpers import expected, fixture, legacy_view, normalized_legacy

PROGRAMS = ["856421092", "816497962", "959312137", "1129129055", "494685723"]
TAX_REFUNDS_MISSED_BEFORE = {"856421092": "6 500 рублей"}


@pytest.mark.parametrize("program_id", PROGRAMS)
def test_parser_matches_previous_site(program_id):
    parsed = legacy_view(parse_details(fixture(f"program-{program_id}.html")))
    reference = normalized_legacy(expected(program_id))
    if program_id in TAX_REFUNDS_MISSED_BEFORE:
        reference["taxRefund"] = TAX_REFUNDS_MISSED_BEFORE[program_id]
    assert parsed == reference


def test_entity_dash_becomes_short_dash():
    details = parse_details(fixture("program-1129129055.html"))
    assert "От материала – к решению" in details.faq[0].answer


def test_literal_dash_is_kept():
    details = parse_details(fixture("program-856421092.html"))
    assert details.schedule == "понедельник и среда, 18:30 — 21:40"


def test_empty_page_gives_empty_details():
    details = parse_details("<html><body></body></html>")
    assert details.modules == []
    assert details.notice is None
    assert details.about == ""
