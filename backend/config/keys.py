from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured

BAD_TWO_FACTOR_KEY = (
    "TWO_FACTOR_KEY должен быть ключом Fernet (32 байта в base64). "
    "Создать новый: openssl rand -base64 32 | tr '+/' '-_'"
)


def check_two_factor_key(key: str) -> str:
    try:
        Fernet(key)
    except ValueError as error:
        raise ImproperlyConfigured(BAD_TWO_FACTOR_KEY) from error
    return key
