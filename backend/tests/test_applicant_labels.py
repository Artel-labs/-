import pytest

from applications.card import facts
from applications.mail import corporate_lines, subject
from applications.models import ApplicantType, Application

pytestmark = pytest.mark.django_db

FIELD = "Кто будет обучаться"


def make_application(kind: str) -> Application:
    return Application.objects.create(
        first_name="Анна", last_name="Иванова", phone="+7 495 000 00 00", email="anna@example.ru", applicant_type=kind
    )


def test_options_are_named_by_who_studies():
    assert ApplicantType.PERSONAL.label == "Частное лицо"
    assert ApplicantType.CORPORATE.label == "Сотрудник организации"
    assert Application._meta.get_field("applicant_type").verbose_name == FIELD


def test_corporate_mail_uses_new_names():
    application = make_application(ApplicantType.CORPORATE)
    assert "(сотрудник организации)" in subject(application)
    assert f"{FIELD}: сотрудник организации (корпоративное обучение)." in corporate_lines(application)


def test_personal_mail_has_no_corporate_note():
    application = make_application(ApplicantType.PERSONAL)
    assert "организации" not in subject(application)
    assert corporate_lines(application) == []


def test_card_shows_the_field_for_corporate_application():
    shown = {fact.title: fact.value for fact in facts(make_application(ApplicantType.CORPORATE))}
    assert shown[FIELD] == "Сотрудник организации"
