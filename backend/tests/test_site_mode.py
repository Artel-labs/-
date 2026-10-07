import re
import runpy

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.site_mode import (
    INSECURE_SMTP,
    NEEDS_COOKIE_SECURE,
    NEEDS_HTTPS_URL,
    PRODUCTION,
    TEST,
    check_site_mode,
    mode_problems,
)

HTTPS_URL = "https://dpo.example.ru"
HTTP_URL = "http://dpo.example.ru"


def test_production_with_https_and_encrypted_mail_is_fine():
    assert mode_problems(PRODUCTION, True, HTTPS_URL, False) == []


def test_production_needs_https():
    assert mode_problems(PRODUCTION, False, HTTP_URL, False) == [NEEDS_COOKIE_SECURE, NEEDS_HTTPS_URL]


def test_production_refuses_insecure_mail():
    assert mode_problems(PRODUCTION, True, HTTPS_URL, True) == [INSECURE_SMTP]


def test_test_mode_allows_http_and_insecure_mail():
    assert mode_problems(TEST, False, HTTP_URL, True) == []


def test_unknown_mode_is_an_error():
    with pytest.raises(ImproperlyConfigured, match="prod"):
        check_site_mode("prod", True, HTTPS_URL, False)


SETTINGS = "config.settings"


def load_settings(monkeypatch, **values: str) -> None:
    monkeypatch.delenv("SMTP_ALLOW_INSECURE_AUTH", raising=False)
    monkeypatch.delenv("SITE_MODE", raising=False)
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    runpy.run_module(SETTINGS)


def load_production(monkeypatch, **overrides: str) -> None:
    load_settings(monkeypatch, **{"COOKIE_SECURE": "1", "SITE_URL": HTTPS_URL, "SITE_MODE": PRODUCTION, **overrides})


def test_production_start_fails_with_insecure_mail(monkeypatch):
    with pytest.raises(ImproperlyConfigured, match=re.escape(INSECURE_SMTP)):
        load_production(monkeypatch, SMTP_ALLOW_INSECURE_AUTH="1")


def test_production_start_fails_without_https(monkeypatch):
    with pytest.raises(ImproperlyConfigured, match=re.escape(NEEDS_COOKIE_SECURE)):
        load_production(monkeypatch, COOKIE_SECURE="0")


def test_production_starts_with_https(monkeypatch):
    load_production(monkeypatch)


def test_missing_mode_means_production(monkeypatch):
    with pytest.raises(ImproperlyConfigured, match=re.escape(NEEDS_COOKIE_SECURE)):
        load_settings(monkeypatch, COOKIE_SECURE="0", SITE_URL=HTTPS_URL)
