from django.core.exceptions import ValidationError

ALLOWED_RECIPIENT_DOMAIN = "hse.ru"
OUTSIDE_DOMAIN = f"Письма с заявками можно отправлять только на адреса @{ALLOWED_RECIPIENT_DOMAIN}."
DOMAIN_HINT = f"Только адрес @{ALLOWED_RECIPIENT_DOMAIN}: в письме все данные заявки."


def in_allowed_domain(email: str) -> bool:
    return email.strip().lower().endswith(f"@{ALLOWED_RECIPIENT_DOMAIN}")


def validate_recipient_domain(email: str) -> None:
    if not in_allowed_domain(email):
        raise ValidationError(OUTSIDE_DOMAIN)
