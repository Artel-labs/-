from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from catalog.models import Program, ProgramTeacher, Source, Teacher
from catalog.presentation.catalog import catalog_page
from catalog.presentation.page import teachers

pytestmark = pytest.mark.django_db

TODAY = date(2026, 10, 6)
NBSP = " "


def make_program(hse_id: str) -> Program:
    return Program.objects.create(
        hse_id=hse_id, title=f"Программа {hse_id}", type_short="ПК", type_title="ПК", source=Source.HSE
    )


def link(program: Program, name: str, position: int) -> None:
    teacher, _ = Teacher.objects.get_or_create(name=name)
    ProgramTeacher.objects.create(program=program, teacher=teacher, position=position)


def compare_teachers(hse_id: str) -> str:
    page = catalog_page(Program.objects.all(), TODAY)
    return next(card.compare.teachers for card in page.cards if card.hse_id == hse_id)


def test_compare_lists_teacher_names_in_programme_order():
    program = make_program("1")
    link(program, "Яковлев Пётр Ильич", 1)
    link(program, f"Андреева{NBSP}Анна Сергеевна", 2)
    link(program, "Руслан Будник", 0)
    assert compare_teachers("1") == "Будник Руслан Александрович · Яковлев Пётр Ильич · Андреева Анна Сергеевна"


def test_compare_names_match_programme_page():
    program = make_program("1")
    link(program, f"Андреева{NBSP}Анна Сергеевна", 0)
    link(program, "Дмитрий Максимов", 1)
    assert compare_teachers("1") == " · ".join(teacher.name for teacher in teachers(program))


def test_compare_is_empty_without_teachers():
    make_program("1")
    assert compare_teachers("1") == ""


def test_catalog_reads_teachers_without_a_query_per_programme():
    for hse_id in ("1", "2", "3"):
        program = make_program(hse_id)
        link(program, f"Преподаватель {hse_id}", 0)
    with CaptureQueriesContext(connection) as few:
        catalog_page(Program.objects.all(), TODAY)
    program = make_program("4")
    link(program, "Преподаватель 4", 0)
    with CaptureQueriesContext(connection) as more:
        catalog_page(Program.objects.all(), TODAY)
    assert len(more.captured_queries) == len(few.captured_queries)
