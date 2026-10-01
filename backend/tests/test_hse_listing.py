from datetime import date

import httpx
import pytest
import respx

from catalog.hse.client import HseClient, HseError, is_hse_url
from catalog.hse.listing import CATALOG_URL, fetch_listing, page_count, page_url, parse_state
from tests.hse_helpers import fixture

FIRST_PAGE_ITEMS = 20
ALL_ITEMS = 24


def test_state_is_parsed_from_page():
    state = parse_state(fixture("listing-page-1.html"))
    assert len(state["items"]) == FIRST_PAGE_ITEMS
    assert state["total"] == ALL_ITEMS
    assert page_count(state) == 2


def test_missing_state_is_reported():
    with pytest.raises(HseError, match="__INITIAL_STATE__"):
        parse_state("<html></html>")


def test_page_urls():
    assert page_url(1) == CATALOG_URL
    assert page_url(2) == f"{CATALOG_URL}&page=2"


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://www.hse.ru/edu/dpo/1", True),
        ("https://pravo.hse.ru/x", True),
        ("http://www.hse.ru/edu/dpo/1", False),
        ("https://hse.ru.evil.com/", False),
        ("https://evilhse.ru/", False),
    ],
)
def test_only_https_hse_hosts_are_allowed(url, allowed):
    assert is_hse_url(url) is allowed


@respx.mock
def test_listing_collects_all_pages():
    respx.get(page_url(1)).respond(200, text=fixture("listing-page-1.html"))
    respx.get(page_url(2)).respond(200, text=fixture("listing-page-2.html"))
    with HseClient() as client:
        programs = fetch_listing(client)
    assert len(programs) == ALL_ITEMS
    english = next(p for p in programs if p.hse_id == "959312137")
    assert english.type_short == "ПК"
    assert english.start_date == date(2026, 10, 2)
    assert english.price == 45000


@respx.mock
def test_redirect_away_from_hse_is_refused():
    respx.get(page_url(1)).respond(302, headers={"Location": "https://example.com/"})
    respx.get("https://example.com/").respond(200, text="")
    with HseClient() as client, pytest.raises(HseError, match="чужой адрес"):
        fetch_listing(client)


@respx.mock
def test_server_error_is_reported():
    respx.get(page_url(1)).respond(503)
    with HseClient() as client, pytest.raises(HseError, match="503"):
        fetch_listing(client)


def test_transport_errors_surface_as_httpx_errors():
    def broken(request):
        raise httpx.ConnectError("нет сети", request=request)

    with HseClient(transport=httpx.MockTransport(broken)) as client, pytest.raises(httpx.ConnectError):
        client.html(CATALOG_URL)
