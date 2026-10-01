import logging
import time
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from analytics.models import Event
from analytics.sanitize import CleanEvent, sanitize

MAX_BATCH = 40
COUNT_CACHE_KEY = "analytics:event-count"
COUNT_CACHE_SECONDS = 60

logger = logging.getLogger(__name__)


def stored_events() -> int:
    count = cache.get(COUNT_CACHE_KEY)
    if count is None:
        count = Event.objects.count()
        cache.set(COUNT_CACHE_KEY, count, COUNT_CACHE_SECONDS)
    return int(count)


def has_room(extra: int) -> bool:
    return stored_events() + extra <= settings.ANALYTICS_MAX_EVENTS


def store(events: list[CleanEvent]) -> None:
    Event.objects.bulk_create(Event(**vars(event)) for event in events)
    cache.set(COUNT_CACHE_KEY, stored_events() + len(events), COUNT_CACHE_SECONDS)


def ingest(raw_events: Any) -> int:
    if not isinstance(raw_events, list):
        return 0
    now_ms = int(time.time() * 1000)
    accepted = [event for raw in raw_events[:MAX_BATCH] if (event := sanitize(raw, now_ms))]
    if not accepted:
        return 0
    if not has_room(len(accepted)):
        logger.warning("Хранилище аналитики заполнено, события отброшены: %s", len(accepted))
        return 0
    store(accepted)
    return len(accepted)


def purge_expired() -> str:
    cutoff = timezone.now() - timedelta(days=settings.ANALYTICS_RETENTION_DAYS)
    deleted, _ = Event.objects.filter(occurred_at__lt=cutoff).delete()
    cache.delete(COUNT_CACHE_KEY)
    return f"Удалено событий: {deleted}"
