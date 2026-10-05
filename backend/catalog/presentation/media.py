from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.storage import default_storage

VERSION_PARAM = "v"


def version(path: Path) -> str:
    return str(int(path.stat().st_mtime)) if path.exists() else ""


def media_url(relative: str) -> str:
    base = default_storage.url(relative)
    stamp = version(Path(settings.MEDIA_ROOT) / relative)
    return f"{base}?{VERSION_PARAM}={stamp}" if stamp else base


def file_url(file: Any) -> str:
    return media_url(file.name)
