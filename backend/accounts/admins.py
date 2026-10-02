from axes.utils import reset
from django.contrib.auth.models import User
from django.db import transaction

from accounts.passwords import new_password

DEFAULT_ADMIN_LOGIN = "admin"


class UnknownAdminError(LookupError):
    pass


def admin_exists() -> bool:
    return User.objects.filter(is_superuser=True).exists()


def admin_logins() -> list[str]:
    return list(User.objects.filter(is_superuser=True).order_by("username").values_list("username", flat=True))


@transaction.atomic
def create_first_admin(login: str = DEFAULT_ADMIN_LOGIN) -> str:
    user = User(username=login, is_staff=True, is_superuser=True)
    password = new_password(user)
    user.set_password(password)
    user.save()
    return password


@transaction.atomic
def reset_admin_password(login: str) -> str:
    user = User.objects.filter(username=login, is_superuser=True).first()
    if user is None:
        raise UnknownAdminError(login)
    password = new_password(user)
    user.set_password(password)
    user.save(update_fields=["password"])
    reset(username=login)
    return password
