from typing import Any

PLAIN_CHARS = str.maketrans({" ": " ", " ": "", "—": "-", "–": "-"})


def untypeset(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(" %", "%").translate(PLAIN_CHARS)
    if isinstance(value, dict):
        return {key: untypeset(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [untypeset(item) for item in value]
    return value
