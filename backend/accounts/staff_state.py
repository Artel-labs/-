from django.contrib.auth.models import User

from accounts import two_factor
from protection.lockout import locked_attempts


def is_locked(user: User) -> bool:
    return bool(locked_attempts().filter(username=user.get_username()).exists())


def has_two_factor(user: User) -> bool:
    return two_factor.is_enabled(user)
