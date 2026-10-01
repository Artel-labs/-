import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from analytics.models import Device, EventType

MAX_PATH = 300
MAX_TITLE = 200
MAX_REFERRER = 200
MAX_TARGET = 500
MAX_LABEL = 120
MAX_SESSION = 64
MIN_SESSION = 8
MAX_LANGUAGE = 16
MAX_CLOCK_SKEW_MS = 48 * 3600 * 1000
MAX_DURATION_MS = 24 * 3600 * 1000
MAX_SCROLL = 100
SESSION_JUNK = re.compile(r"[^a-zA-Z0-9_-]")
TYPES = set(EventType.values)
DEVICES = set(Device.values)


@dataclass(frozen=True)
class CleanEvent:
    occurred_at: datetime
    session: str
    type: str
    path: str
    title: str
    referrer: str
    target: str
    label: str
    duration_ms: int
    device: str
    language: str
    scroll: int


def clamp_text(value: Any, limit: int) -> str:
    text = "" if value is None else str(value).strip()
    return text[:limit]


def number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if result == result and abs(result) != float("inf") else 0.0


def bounded(value: Any, upper: int) -> int:
    return int(max(0.0, min(number(value), float(upper))))


def moment(raw: Any, now_ms: int) -> datetime:
    timestamp = number(raw)
    if not timestamp or abs(timestamp - now_ms) > MAX_CLOCK_SKEW_MS:
        timestamp = now_ms
    return datetime.fromtimestamp(timestamp / 1000, tz=UTC)


def sanitize(raw: Any, now_ms: int) -> CleanEvent | None:
    if not isinstance(raw, dict):
        return None
    event_type = str(raw.get("type") or "").lower()
    session = SESSION_JUNK.sub("", clamp_text(raw.get("sid"), MAX_SESSION))
    path = clamp_text(raw.get("path") or "/", MAX_PATH)
    if event_type not in TYPES or len(session) < MIN_SESSION or not path.startswith("/"):
        return None
    device = raw.get("device")
    return CleanEvent(
        occurred_at=moment(raw.get("t"), now_ms),
        session=session,
        type=event_type,
        path=path,
        title=clamp_text(raw.get("title"), MAX_TITLE),
        referrer=clamp_text(raw.get("ref"), MAX_REFERRER),
        target=clamp_text(raw.get("target"), MAX_TARGET),
        label=clamp_text(raw.get("label"), MAX_LABEL),
        duration_ms=bounded(raw.get("ms"), MAX_DURATION_MS),
        device=device if device in DEVICES else Device.DESKTOP,
        language=clamp_text(raw.get("lang"), MAX_LANGUAGE),
        scroll=bounded(raw.get("scroll"), MAX_SCROLL),
    )
