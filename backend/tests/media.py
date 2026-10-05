import re
from typing import Any

VERSION = re.compile(r"\?v=\d+")


def unversioned(value: Any) -> Any:
    if isinstance(value, str):
        return VERSION.sub("", value)
    if isinstance(value, dict):
        return {key: unversioned(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [unversioned(item) for item in value]
    return value
