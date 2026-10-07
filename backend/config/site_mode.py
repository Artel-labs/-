from django.core.exceptions import ImproperlyConfigured

PRODUCTION = "production"
TEST = "test"
MODES = frozenset({PRODUCTION, TEST})
HTTPS_PREFIX = "https://"
UNKNOWN_MODE = "SITE_MODE должен быть production или test, сейчас: «{mode}»."
NEEDS_COOKIE_SECURE = (
    "Боевой режим (SITE_MODE=production) работает только по HTTPS, а COOKIE_SECURE не равен 1. "
    "Включите HTTPS: sudo ./scripts/setup-https.sh"
)
NEEDS_HTTPS_URL = "Боевой режим (SITE_MODE=production): SITE_URL должен начинаться с https://."
INSECURE_SMTP = (
    "Боевой режим (SITE_MODE=production): SMTP_ALLOW_INSECURE_AUTH=1 запрещён, "
    "письма с заявками уходят только с шифрованием."
)


def production_problems(cookie_secure: bool, site_url: str, insecure_smtp: bool) -> list[str]:
    checks = (
        (not cookie_secure, NEEDS_COOKIE_SECURE),
        (not site_url.startswith(HTTPS_PREFIX), NEEDS_HTTPS_URL),
        (insecure_smtp, INSECURE_SMTP),
    )
    return [message for failed, message in checks if failed]


def mode_problems(mode: str, cookie_secure: bool, site_url: str, insecure_smtp: bool) -> list[str]:
    if mode not in MODES:
        return [UNKNOWN_MODE.format(mode=mode)]
    return production_problems(cookie_secure, site_url, insecure_smtp) if mode == PRODUCTION else []


def check_site_mode(mode: str, cookie_secure: bool, site_url: str, insecure_smtp: bool) -> None:
    if problems := mode_problems(mode, cookie_secure, site_url, insecure_smtp):
        raise ImproperlyConfigured(" ".join(problems))
