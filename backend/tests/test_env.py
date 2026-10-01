import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import env_flag, env_int, env_list, env_required

NAME = "DPO_TEST_VARIABLE"


def test_required_value_is_returned(monkeypatch):
    monkeypatch.setenv(NAME, " секрет ")
    assert env_required(NAME) == "секрет"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_required_value_stops_start(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(NAME, raising=False)
    else:
        monkeypatch.setenv(NAME, value)
    with pytest.raises(ImproperlyConfigured, match=NAME):
        env_required(NAME)


FLAG_CASES = [("1", True), ("true", True), ("Yes", True), ("0", False), ("no", False)]


@pytest.mark.parametrize(("value", "expected"), FLAG_CASES)
def test_flag_is_parsed(monkeypatch, value, expected):
    monkeypatch.setenv(NAME, value)
    assert env_flag(NAME) is expected


def test_flag_falls_back_to_default(monkeypatch):
    monkeypatch.delenv(NAME, raising=False)
    assert env_flag(NAME, default=True) is True


def test_list_drops_blanks_and_spaces(monkeypatch):
    monkeypatch.setenv(NAME, " a.ru, ,b.ru ,")
    assert env_list(NAME) == ["a.ru", "b.ru"]


def test_int_uses_default_when_missing(monkeypatch):
    monkeypatch.delenv(NAME, raising=False)
    assert env_int(NAME, 3306) == 3306
