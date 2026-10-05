from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from accounts import two_factor


def is_locked(user: User) -> bool:
    since = timezone.now() - settings.LOGIN_COOLOFF
    attempts = AccessAttempt.objects.filter(username=user.get_username(), attempt_time__gte=since)
    return bool(attempts.filter(failures_since_start__gte=settings.LOGIN_FAILURE_LIMIT).exists())


def has_two_factor(user: User) -> bool:
    return two_factor.is_enabled(user)
