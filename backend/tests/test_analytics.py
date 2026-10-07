import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from analytics.models import Event
from analytics.sanitize import sanitize
from analytics.service import MAX_BATCH, purge_expired
from analytics.summary import Summary, build_summary

pytestmark = pytest.mark.django_db

FIXTURES = Path(__file__).parent / "fixtures"
EVENTS = json.loads((FIXTURES / "analytics_events.json").read_text(encoding="utf-8"))
LEGACY = json.loads((FIXTURES / "legacy_analytics_summary.json").read_text(encoding="utf-8"))
NOW_MS = EVENTS["now"]
NOW = datetime.fromtimestamp(NOW_MS / 1000, tz=UTC)
DAY_MS = 86_400_000
KPI_FIELDS = (
    "visitors",
    "visitors_today",
    "pageviews",
    "pageviews_today",
    "avg_duration_ms",
    "avg_pages",
    "bounce_rate",
)
LEGACY_KPIS = ("visitors", "visitorsToday", "pageviews", "pageviewsToday", "avgDurationMs", "avgPages", "bounceRate")
TOP_FIELDS = ("top_pages", "top_programs", "top_filters", "top_referrers", "top_paths")
LEGACY_TOPS = ("topPages", "topPrograms", "topFilters", "topReferrers", "topPaths")


@pytest.fixture(autouse=True)
def fresh_cache():
    cache.clear()


def event(**fields: Any) -> dict[str, Any]:
    return {"t": NOW_MS, "sid": "abcdefgh12", "type": "pageview", "path": "/", "device": "mobile", **fields}


def stored(raw: dict[str, Any]) -> Event:
    clean = sanitize(raw, raw["t"])
    assert clean is not None
    return Event(**vars(clean))


def rows(items: list[Any]) -> list[dict[str, Any]]:
    return [{"name": item.name, "count": item.count} for item in items]


def legacy_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"name": item["name"], "count": item["count"]} for item in items]


def summary_record(summary: Summary) -> dict[str, Any]:
    return {
        "kpis": [*(getattr(summary, name) for name in KPI_FIELDS), summary.program_clicks],
        "devices": {row.name: row.count for row in summary.devices},
        "hours": summary.hours,
        "daily": [{"day": row.name, "pageviews": row.count} for row in summary.daily],
        "top": [rows(getattr(summary, name)) for name in TOP_FIELDS],
        "interest": [{"name": row.name, "count": pytest.approx(row.count)} for row in summary.top_interest],
        "scroll": [vars(row) for row in summary.scroll_depth],
        "sessions": [{**vars(row), "startedAt": None} for row in summary.recent_sessions],
        "insights": summary.insights,
    }


def legacy_session(item: dict[str, Any]) -> dict[str, Any]:
    fields = {key: item[key] for key in ("sid", "device", "pages", "path", "programs")}
    return {**fields, "duration_ms": item["durationMs"], "startedAt": None}


def legacy_record(legacy: dict[str, Any]) -> dict[str, Any]:
    kpis = legacy["kpis"]
    return {
        "kpis": [*(kpis[key] for key in LEGACY_KPIS), kpis["programClicks"]],
        "devices": legacy["devices"],
        "hours": legacy["hours"],
        "daily": legacy["daily"],
        "top": [legacy_rows(legacy[key]) for key in LEGACY_TOPS],
        "interest": legacy_rows(legacy["topInterest"]),
        "scroll": legacy["scrollDepth"],
        "sessions": [legacy_session(item) for item in legacy["recentSessions"]],
        "insights": legacy["insights"],
    }


@pytest.mark.parametrize("days", [7, 30, 90])
def test_summary_matches_previous_site(days):
    events = [stored(raw) for raw in EVENTS["events"] if raw["t"] >= NOW_MS - days * DAY_MS]
    assert summary_record(build_summary(events, NOW, days)) == legacy_record(LEGACY[str(days)])


def test_empty_summary_explains_how_data_appears():
    summary = build_summary([], NOW, 7)
    assert summary.visitors == 0
    assert summary.insights == ["Пока нет данных. События появятся, когда посетители разрешат статистику в баннере."]


def test_sanitize_rejects_foreign_events():
    assert sanitize(event(type="compare_open"), NOW_MS) is None
    assert sanitize(event(sid="short"), NOW_MS) is None
    assert sanitize(event(path="https://evil.example/"), NOW_MS) is None
    assert sanitize("pageview", NOW_MS) is None


def test_sanitize_clamps_values():
    raw = event(t=NOW_MS - 72 * 3600 * 1000, device="fridge", ms=-5, scroll=250, label="x" * 500, sid="ab cd<ef>gh!")
    clean = sanitize(raw, NOW_MS)
    assert clean is not None
    assert clean.occurred_at == NOW
    assert clean.device == "desktop"
    assert (clean.duration_ms, clean.scroll, len(clean.label), clean.session) == (0, 100, 120, "abcdefgh")


def test_collect_stores_batch(client):
    batch = [event(sid=f"session{index:04d}") for index in range(MAX_BATCH + 5)]
    response = client.post("/api/collect", json.dumps({"events": batch}), content_type="application/json")
    assert response.status_code == 204
    assert Event.objects.count() == MAX_BATCH


def test_collect_accepts_plain_list_and_skips_junk(client):
    response = client.post("/api/collect", json.dumps([event(), event(type="nope")]), content_type="application/json")
    assert response.status_code == 204
    assert Event.objects.count() == 1


def test_collect_rejects_foreign_origin_and_bad_json(client):
    payload = json.dumps({"events": [event()]})
    foreign = client.post("/api/collect", payload, content_type="application/json", HTTP_ORIGIN="https://evil.example")
    assert foreign.status_code == 403
    assert client.post("/api/collect", "{", content_type="application/json").status_code == 400
    assert Event.objects.count() == 0


def test_collect_respects_storage_limit(client, settings):
    settings.ANALYTICS_MAX_EVENTS = 2
    for _ in range(2):
        client.post("/api/collect", json.dumps([event(), event()]), content_type="application/json")
    assert Event.objects.count() == 2


def test_purge_removes_expired_events(settings):
    settings.ANALYTICS_RETENTION_DAYS = 90
    old = stored(event())
    old.occurred_at = timezone.now() - timedelta(days=91)
    fresh = stored(event())
    fresh.occurred_at = timezone.now()
    Event.objects.bulk_create([old, fresh])
    assert purge_expired() == "Удалено событий: 1"
    assert Event.objects.count() == 1


def test_dashboard_shows_summary_to_staff(client):
    admin = get_user_model().objects.create_superuser("boss", "boss@example.ru", "a-long-password-1")
    client.force_login(admin)
    Event.objects.bulk_create([stored(event(t=int(timezone.now().timestamp() * 1000)))])
    response = client.get("/admin/analytics/event/?days=30")
    assert response.status_code == 200
    page = response.content.decode()
    assert "Посещаемость" in page
    assert "Посетители за период" in page
    assert "период 30 дн." in page


def test_dashboard_requires_login(client):
    assert client.get("/admin/analytics/event/").status_code == 302
