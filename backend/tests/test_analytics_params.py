import json
from importlib import import_module
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.utils import timezone

from analytics.models import Event
from analytics.sanitize import KEPT_PARAMS, page_path, sanitize

pytestmark = pytest.mark.django_db

SHARED = json.loads((Path(__file__).parents[2] / "shared" / "analytics-params.json").read_text(encoding="utf-8"))
NOW_MS = 1_790_000_000_000


def clean_path(path: str) -> str:
    event = sanitize({"t": NOW_MS, "sid": "abcdefgh12", "type": "pageview", "path": path}, NOW_MS)
    assert event is not None
    return event.path


def test_email_in_address_is_not_stored_but_utm_is():
    assert clean_path("/?email=a@b.ru&utm_source=tg") == "/?utm_source=tg"


def test_page_without_utm_is_stored_as_bare_path():
    assert clean_path("/programs/x.html?phone=79990000000&name=Ivan#top") == "/programs/x.html"


def test_all_utm_parameters_are_kept():
    assert page_path("/?utm_source=s&a=1&utm_medium=m&utm_campaign=c") == "/?utm_source=s&utm_medium=m&utm_campaign=c"


def test_address_must_still_start_with_slash():
    event = sanitize({"t": NOW_MS, "sid": "abcdefgh12", "type": "pageview", "path": "https://evil.example/x"}, NOW_MS)
    assert event is None


def test_server_and_browser_keep_the_same_parameters():
    assert list(KEPT_PARAMS) == SHARED["kept"]


def stored(path: str) -> Event:
    return Event.objects.create(
        occurred_at=timezone.now(), session="abcdefgh12", type="pageview", path=path, device="desktop"
    )


def test_migration_cleans_stored_events():
    stored(path="/?email=a@b.ru&utm_campaign=x")
    stored(path="/catalog")
    import_module("analytics.migrations.0003_strip_page_query").strip_page_query(django_apps, None)
    assert sorted(Event.objects.values_list("path", flat=True)) == ["/?utm_campaign=x", "/catalog"]
