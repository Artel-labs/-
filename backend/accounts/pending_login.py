import time
from dataclasses import asdict, dataclass

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import User
from django.http import HttpRequest

PENDING_KEY = "two_factor_pending"
PENDING_SECONDS = 300


@dataclass(frozen=True)
class PendingLogin:
    user_id: str
    backend: str
    redirect_to: str
    until: float


def remember(request: HttpRequest, user: AbstractBaseUser, backend: str, redirect_to: str) -> None:
    login = PendingLogin(str(user.pk), backend, redirect_to, time.time() + PENDING_SECONDS)
    request.session[PENDING_KEY] = asdict(login)


def forget(request: HttpRequest) -> None:
    request.session.pop(PENDING_KEY, None)


def pending(request: HttpRequest) -> PendingLogin | None:
    data = request.session.get(PENDING_KEY)
    if not data:
        return None
    login = PendingLogin(**data)
    if login.until < time.time():
        forget(request)
        return None
    return login


def pending_user(login: PendingLogin) -> User | None:
    return User.objects.filter(pk=login.user_id, is_active=True, is_staff=True).first()
