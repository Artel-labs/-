import os

from django.core.exceptions import ImproperlyConfigured

TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def env_text(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_required(name: str) -> str:
    value = env_text(name)
    if not value:
        raise ImproperlyConfigured(f"Не задана переменная окружения {name}")
    return value


def env_flag(name: str, default: bool = False) -> bool:
    value = env_text(name)
    if not value:
        return default
    return value.lower() in TRUE_VALUES


def env_int(name: str, default: int) -> int:
    value = env_text(name)
    return int(value) if value else default


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env_text(name, default).split(",") if item.strip()]
