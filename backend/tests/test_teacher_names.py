import json
from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command

from catalog.models import Program
from catalog.presentation.landing.names import is_patronymic, parse_name
from catalog.presentation.landing.page import landing_page

DAY = date(2026, 10, 1)

CASES = [
    ("Максимов Дмитрий Михайлович", "Максимов Дмитрий", "Максимов Дмитрий Михайлович", "ДМ"),
    ("Дарья Александровна Ждан-Пушкина", "Ждан-Пушкина Дарья", "Ждан-Пушкина Дарья Александровна", "ДЖ"),
    ("Анастасия Албух", "Албух Анастасия", "Албух Анастасия", "АА"),
    ("Наталия Ковалева", "Ковалева Наталия", "Ковалева Наталия", "НК"),
    ("Ван Лисюань", "Ван Лисюань", "Ван Лисюань", "ЛВ"),
    ("Чжан Цин", "Чжан Цин", "Чжан Цин", "ЦЧ"),
    ("Дюфло Алан / Duflot Alain", "Дюфло Алан", "Дюфло Алан / Duflot Alain", "АД"),
    ("Александра Петровна Илькевич", "Илькевич Александра", "Илькевич Александра Петровна", "АИ"),
    ("Илькевич Александра Петровна", "Илькевич Александра", "Илькевич Александра Петровна", "АИ"),
    ("Синельникова Валентина Николаевна", "Синельникова Валентина", "Синельникова Валентина Николаевна", "ВС"),
]


@pytest.mark.parametrize(("raw", "short", "full", "initials"), CASES)
def test_name_is_shown_surname_first(raw, short, full, initials):
    name = parse_name(raw)
    assert (name.short, name.full, name.initials) == (short, full, initials)


def test_patronymic_endings():
    assert all(is_patronymic(word) for word in ("Михайлович", "Николаевна", "Кузьминична", "Ильич"))
    assert not any(is_patronymic(word) for word in ("Максимов", "Дарья", "Лисюань"))


def test_unknown_layout_keeps_the_original_order():
    assert parse_name("Кто-то Совсем Странный").short == "Кто-то Совсем Странный"
    assert parse_name("Платон").full == "Платон"


@pytest.fixture
def cards(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())
    return landing_page(Program.objects.filter(is_published=True), DAY).teachers


@pytest.mark.django_db
def test_every_landing_name_is_surname_and_given_name_only(cards):
    assert cards
    for card in cards:
        assert len(card.name.split()) <= 2, card.name
        assert "/" not in card.name


@pytest.mark.django_db
def test_card_window_shows_the_full_name_starting_with_the_short_one(cards):
    for card in cards:
        assert json.loads(card.payload)["name"].startswith(card.name)
        assert card.more_label == f"Подробнее: {card.name}"
