import time

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone

from accounts.models import TwoFactor
from accounts.secret_box import seal
from accounts.totp import matching_step, new_secret


def device_of(user: AbstractBaseUser) -> TwoFactor | None:
    return TwoFactor.objects.filter(user_id=user.pk).first()


def protected_logins() -> list[str]:
    return list(TwoFactor.objects.order_by("user__username").values_list("user__username", flat=True))


def is_enabled(user: AbstractBaseUser) -> bool:
    device = device_of(user)
    return bool(device and device.enabled)


def start(user: AbstractBaseUser) -> TwoFactor:
    device, _ = TwoFactor.objects.get_or_create(user_id=user.pk, defaults={"sealed_secret": seal(new_secret())})
    if not device.enabled:
        device.secret = new_secret()
        device.last_step = 0
        device.save(update_fields=["sealed_secret", "last_step"])
    return device


@transaction.atomic
def accept_code(device: TwoFactor, code: str) -> bool:
    locked = TwoFactor.objects.select_for_update().get(pk=device.pk)
    step = matching_step(locked.secret, code, time.time(), locked.last_step)
    if step is None:
        return False
    locked.last_step = step
    locked.save(update_fields=["last_step"])
    return True


def confirm(user: AbstractBaseUser, code: str) -> bool:
    device = device_of(user)
    if device is None or device.enabled or not accept_code(device, code):
        return False
    device.refresh_from_db()
    device.confirmed_at = timezone.now()
    device.save(update_fields=["confirmed_at"])
    return True


def disable(user: AbstractBaseUser, code: str) -> bool:
    device = device_of(user)
    if device is None or not device.enabled or not accept_code(device, code):
        return False
    device.delete()
    return True


def reset(user: AbstractBaseUser) -> bool:
    deleted, _ = TwoFactor.objects.filter(user_id=user.pk).delete()
    return deleted > 0
