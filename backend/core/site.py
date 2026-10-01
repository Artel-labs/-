from django.conf import settings

SHARE_IMAGE_PATH = "/images/hero-composite.jpg"


def absolute_url(path: str) -> str:
    return f"{settings.SITE_URL}{path}"
