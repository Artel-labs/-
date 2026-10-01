import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import json5

from catalog.hse.client import HseClient, HseError, is_hse_url

CATALOG_URL = "https://www.hse.ru/edu/dpo/?orgUnit=22753"
MAX_PAGES = 20
MOSCOW = ZoneInfo("Europe/Moscow")
MILLISECONDS = 1000
INITIAL_STATE = re.compile(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*window\.__URQL_DATA__", re.S)
JS_DATE = re.compile(r"new Date\((-?\d+)\)")


@dataclass(frozen=True)
class ListedProgram:
    hse_id: str
    title: str
    url: str
    type_short: str
    type_title: str
    study_format: str
    duration: str
    start_date: date | None
    start_month_only: bool
    price: int | None
    base_price: int | None


def parse_state(html: str) -> dict[str, Any]:
    match = INITIAL_STATE.search(html)
    if not match:
        raise HseError("На странице каталога hse.ru не найден window.__INITIAL_STATE__ — разметка изменилась")
    state: dict[str, Any] = json5.loads(JS_DATE.sub(r"\1", match.group(1)))
    return state


def page_url(page: int, base: str = CATALOG_URL) -> str:
    parts = urlsplit(base)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key != "page"]
    if page > 1:
        query.append(("page", str(page)))
    return urlunsplit(parts._replace(query=urlencode(query)))


def moscow_date(timestamp: int | None) -> date | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp / MILLISECONDS, MOSCOW).date()


def listed_program(item: dict[str, Any]) -> ListedProgram:
    kind = item.get("type") or {}
    study_format = item.get("studyFormat") or {}
    return ListedProgram(
        hse_id=str(item["id"]),
        title=" ".join(str(item.get("title") or "").split()),
        url=str(item["url"]),
        type_short=kind.get("shortTitle") or kind.get("title") or "",
        type_title=kind.get("title") or kind.get("shortTitle") or "",
        study_format=study_format.get("title") or "",
        duration=item.get("duration") or "",
        start_date=moscow_date(item.get("startDate")),
        start_month_only=bool(item.get("isStartDateWithoutDay")),
        price=item.get("discountPrice"),
        base_price=item.get("educationPricing"),
    )


def page_count(state: dict[str, Any]) -> int:
    items = state.get("items") or []
    total = int(state.get("total") or len(items))
    size = int(state.get("pageSize") or len(items) or 1)
    return min(MAX_PAGES, max(1, -(-total // size)))


def fetch_listing(client: HseClient) -> list[ListedProgram]:
    first = parse_state(client.html(page_url(1)))
    items = {str(item["id"]): item for item in first.get("items") or []}
    for page in range(2, page_count(first) + 1):
        state = parse_state(client.html(page_url(page)))
        items.update({str(item["id"]): item for item in state.get("items") or []})
    programs = [listed_program(item) for item in items.values() if is_hse_url(str(item.get("url") or ""))]
    if not programs:
        raise HseError("hse.ru не вернул ни одной программы с корректной ссылкой — обновление отменено")
    return programs
