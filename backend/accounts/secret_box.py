from functools import cache

from cryptography.fernet import Fernet
from django.conf import settings

SEALED_PREFIX = "gAAAAA"


@cache
def box() -> Fernet:
    return Fernet(settings.TWO_FACTOR_KEY)


def seal(text: str) -> str:
    return box().encrypt(text.encode()).decode()


def unseal(token: str) -> str:
    return box().decrypt(token.encode()).decode()


def is_sealed(value: str) -> bool:
    return value.startswith(SEALED_PREFIX)
