from datetime import date

import pytest

from catalog.models import Program, Source
from catalog.presentation.catalog import catalog_page
from catalog.presentation.landing.groups import Grouped
from catalog.presentation.landing.menu import menu
from catalog.presentation.text import plural_programs

TODAY = date(2026, 10, 6)


@pytest.mark.parametrize(
    ("count", "label"),
    [
        (1, "1 программа"),
        (3, "3 программы"),
        (11, "11 программ"),
        (21, "21 программа"),
        (34, "34 программы"),
        (35, "35 программ"),
    ],
)
def test_programs_label_agrees_with_number(count, label):
    assert plural_programs(count) == label


def test_landing_menu_names_all_programs_with_agreement():
    assert menu(Grouped(spheres=[], unassigned=[]), 34).total_label == "34 программы"


@pytest.mark.django_db
def test_catalog_page_names_its_programs_with_agreement():
    for hse_id in ("1", "2"):
        Program.objects.create(hse_id=hse_id, title=f"Программа {hse_id}", type_short="ПК", source=Source.HSE)
    page = catalog_page(Program.objects.all(), TODAY)
    assert (page.total, page.total_label) == (2, "2 программы")
