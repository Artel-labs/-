import re
import runpy
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from accounts import two_factor
from accounts.models import TwoFactor
from accounts.secret_box import is_sealed
from accounts.totp import new_secret
from config.keys import BAD_TWO_FACTOR_KEY, check_two_factor_key
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

MIGRATION = "accounts.migrations.0003_seal_two_factor_secret"


def raw_value(device: TwoFactor) -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT sealed_secret FROM accounts_twofactor WHERE id = %s", [device.pk])
        return str(cursor.fetchone()[0])


def test_database_keeps_only_sealed_secret():
    device = two_factor.start(make_admin())
    stored = raw_value(device)
    assert is_sealed(stored)
    assert device.secret not in stored
    assert TwoFactor.objects.get(pk=device.pk).secret == device.secret


def test_migration_seals_plain_secrets_once():
    device = two_factor.start(make_admin())
    plain = new_secret()
    TwoFactor.objects.filter(pk=device.pk).update(sealed_secret=plain)
    seal_secrets = import_module(MIGRATION).seal_secrets
    seal_secrets(django_apps, None)
    sealed_once = raw_value(device)
    seal_secrets(django_apps, None)
    assert is_sealed(sealed_once)
    assert raw_value(device) == sealed_once
    assert TwoFactor.objects.get(pk=device.pk).secret == plain


def test_migration_can_be_reversed():
    device = two_factor.start(make_admin())
    plain = TwoFactor.objects.get(pk=device.pk).secret
    import_module(MIGRATION).unseal_secrets(django_apps, None)
    assert raw_value(device) == plain


def test_bad_key_is_refused():
    with pytest.raises(ImproperlyConfigured, match=re.escape(BAD_TWO_FACTOR_KEY)):
        check_two_factor_key("not-a-key")


def test_site_does_not_start_without_key(monkeypatch):
    monkeypatch.delenv("TWO_FACTOR_KEY", raising=False)
    with pytest.raises(ImproperlyConfigured, match="TWO_FACTOR_KEY"):
        runpy.run_module("config.settings")
