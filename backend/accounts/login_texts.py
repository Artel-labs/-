from django.conf import settings

SECONDS_PER_MINUTE = 60


def locked_message() -> str:
    minutes = int(settings.LOGIN_COOLOFF.total_seconds() // SECONDS_PER_MINUTE)
    return f"Слишком много неверных попыток. Попробуйте снова через {minutes}\u00a0мин."
