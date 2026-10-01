import secrets
import string

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

GENERATED_PASSWORD_LENGTH = 20
PASSWORD_ALPHABET = string.ascii_letters + string.digits


def new_password(user: User) -> str:
    password = "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(GENERATED_PASSWORD_LENGTH))
    validate_password(password, user)
    return password
