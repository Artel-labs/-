from datetime import date, timedelta
from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

from catalog.hse.listing import ListedProgram
from catalog.models import TOP_PLACES, Program, Source
from catalog.presentation.cards import card
from catalog.presentation.landing.top import picked
from catalog.presentation.page import program_page
from catalog.sync.fields import apply_listing
from catalog.top_picks import HIGH_RATING, pin_high_rating
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

TODAY = date(2026, 10, 6)
OK = 200


def make_program(hse_id: str, days: int | None = None, top: int | None = None) -> Program:
    return Program.objects.create(
        hse_id=hse_id,
        title=f"Программа {hse_id}",
        type_short="ПК",
        type_title="ПК",
        study_format="Очный",
        source=Source.HSE,
        start_date=TODAY + timedelta(days=days) if days is not None else None,
        top_position=top,
    )


def ids(programs: list[Program]) -> list[str]:
    return [program.hse_id for program in programs]


def test_rated_programs_go_in_their_order():
    programs = [
        make_program("1", days=5),
        make_program("2", top=2),
        make_program("3", top=1),
        make_program("4", days=1),
    ]
    assert ids(picked(programs, TODAY)) == ["3", "2"]


def test_block_has_no_programs_without_high_rating():
    programs = [make_program("1"), make_program("2", days=30), make_program("3", days=-3)]
    assert picked(programs, TODAY) == []


def test_block_shows_at_most_seven_programs():
    programs = [make_program(str(number), days=number, top=1) for number in range(TOP_PLACES + 3)]
    assert len(picked(programs, TODAY)) == TOP_PLACES == 7


def test_high_rating_follows_the_place():
    assert make_program("1", top=4).high_rating
    assert not make_program("2").high_rating


def test_pinning_marks_only_the_chosen_programs():
    stale = make_program("1", top=1)
    chosen = make_program(HIGH_RATING[2])
    pin_high_rating(Program.objects)
    stale.refresh_from_db()
    chosen.refresh_from_db()
    assert stale.top_position is None
    assert chosen.top_position == 3


def test_catalog_card_tells_high_rating():
    assert card(make_program("1", top=2), TODAY).high_rating
    assert not card(make_program("2"), TODAY).high_rating


def test_place_must_fit_the_block():
    program = make_program("1", top=TOP_PLACES + 1)
    with pytest.raises(ValidationError):
        program.full_clean()


def test_seed_pins_initial_programs(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())
    pinned = Program.objects.exclude(top_position=None).order_by("top_position")
    assert [(program.hse_id, program.top_position) for program in pinned] == [
        (hse_id, place) for place, hse_id in enumerate(HIGH_RATING, start=1)
    ]


def test_program_page_tells_high_rating(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())
    rated = Program.objects.get(hse_id=HIGH_RATING[0])
    plain = Program.objects.filter(top_position=None).first()
    assert program_page(rated, TODAY).high_rating
    assert plain is not None
    assert not program_page(plain, TODAY).high_rating


def test_place_is_editable_for_hse_program(client):
    client.force_login(make_admin())
    program = make_program("1")
    response = client.get(f"/admin/catalog/program/{program.pk}/change/")
    assert response.status_code == OK
    html = response.content.decode()
    assert 'name="top_position"' in html
    assert "место в блоке «Программы с высоким рейтингом» и обложку" in html
    assert "Высокий рейтинг: место на главной (1–7)" in html


def test_sync_keeps_the_place():
    program = make_program("1", top=3)
    listed = ListedProgram("1", program.title, "https://hse.ru/p", "ПК", "ПК", "Очный", "", None, False, None, None)
    apply_listing(program, listed, {})
    assert program.top_position == 3
