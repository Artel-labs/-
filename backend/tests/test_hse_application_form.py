import pytest

from catalog.hse.details import ProgramDetails, parse_details
from catalog.models import Program, Source
from catalog.sync.fields import SYNCED_FIELDS, apply_details

FORM = 856420964
QUESTION_FORM = 856421060
WIDGET = "https://www.hse.ru/n/exp/widgets/widgetPassExpressPoll"
PAGE = f"""
<html><body>
<div class="modal" id="modal-application"><div class="modal__content" id="modal-application-content">
<script src="{WIDGET}/{FORM}.js"></script></div></div>
<div class="modal" id="modal-form"><div class="modal__content" id="modal-form-content">
<script src="{WIDGET}/{QUESTION_FORM}.js"></script></div></div>
</body></html>
"""


def program(**fields) -> Program:
    defaults = {"hse_id": "856421092", "title": "Английское контрактное право", "type_short": "ПК"}
    return Program.objects.create(source=Source.HSE, type_title="ПК", study_format="Очный", **{**defaults, **fields})


def test_form_number_comes_from_the_application_window():
    assert parse_details(PAGE).application_form_id == FORM


def test_page_without_application_window_has_no_form():
    assert parse_details("<html><body></body></html>").application_form_id is None


def test_form_number_follows_hse():
    assert "application_form_id" in SYNCED_FIELDS


@pytest.mark.django_db
def test_sync_stores_new_form_and_keeps_known_one_when_page_has_none():
    saved = program()
    apply_details(saved, ProgramDetails(application_form_id=FORM))
    assert saved.application_form_id == FORM
    apply_details(saved, ProgramDetails())
    assert saved.application_form_id == FORM


@pytest.mark.django_db
def test_program_options_carry_form_and_hse_page(client):
    program(application_form_id=FORM, hse_url="https://www.hse.ru/edu/dpo/856421092")
    program(hse_id="1", title="Без формы")
    options = {item["id"]: item for item in client.get("/api/catalog/program-options").json()}
    assert options["856421092"]["form"] == FORM
    assert options["856421092"]["hse_url"] == "https://www.hse.ru/edu/dpo/856421092"
    assert options["1"]["form"] is None
