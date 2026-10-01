import json
import smtplib
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from applications.mail import letter, send_application_mail, subject
from applications.models import Application, MailStatus, Status
from applications.rules import email_looks_valid, phone_problem
from applications.service import purge_expired

pytestmark = pytest.mark.django_db

URL = "/api/applications"
FIXTURES = Path(__file__).parent / "fixtures"
CASES = json.loads((Path(__file__).parents[2] / "shared" / "form-rules-cases.json").read_text(encoding="utf-8"))
VALID = {
    "firstName": "Иван",
    "lastName": "Петров",
    "phone": "+7 (495) 772-95-90",
    "email": "ivan@example.ru",
    "consent": True,
    "programId": "856421092",
    "programTitle": "Название из браузера",
    "sources": ["search", "other", "search", "unknown"],
    "sourceOther": "друзья",
    "comment": "Первая строка\r\n\r\n\r\nВторая",
}


@pytest.fixture
def mailing(settings):
    settings.EMAIL_HOST = "smtp.example.ru"
    settings.APPLICATION_MAIL_TO = ["office@example.ru"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())


def post(client, payload, **headers):
    return client.post(URL, payload, content_type="application/json", **headers)


@pytest.mark.parametrize(("value", "valid"), CASES["email"])
def test_email_rule(value, valid):
    assert email_looks_valid(value) is valid


@pytest.mark.parametrize(("value", "problem"), CASES["phone"])
def test_phone_rule(value, problem):
    assert phone_problem(value) == problem


def test_valid_application_is_saved_and_mail_queued(client, seeded, mailing, django_capture_on_commit_callbacks):
    with patch("applications.service.async_task") as queued, django_capture_on_commit_callbacks(execute=True):
        response = post(client, VALID)
    assert response.status_code == 200
    saved = Application.objects.get(pk=response.json()["id"])
    assert saved.program_title == "Английское контрактное право"
    assert saved.sources == ["search", "other"]
    assert saved.source_other == "друзья"
    assert saved.comment == "Первая строка\n\nВторая"
    assert saved.status == Status.NEW
    assert saved.mail_status == MailStatus.QUEUED
    queued.assert_called_once()


def test_without_mail_settings_application_is_still_accepted(client, settings):
    settings.EMAIL_HOST = ""
    response = post(client, {**VALID, "programId": ""})
    assert response.status_code == 200
    assert Application.objects.get().mail_status == MailStatus.SKIPPED


def test_repeat_within_ten_minutes_returns_same_application(client):
    first = post(client, VALID).json()["id"]
    second = post(client, {**VALID, "email": "IVAN@example.ru", "phone": "+7 495 772 95 90"}).json()["id"]
    assert first == second
    assert Application.objects.count() == 1


def test_repeat_after_ten_minutes_is_new_application(client):
    first = post(client, VALID).json()["id"]
    Application.objects.filter(pk=first).update(received_at=timezone.now() - timedelta(minutes=11))
    assert post(client, VALID).json()["id"] != first


def test_missing_fields_are_reported(client):
    response = post(client, {"phone": "12", "email": "bad"})
    assert response.status_code == 400
    assert response.json()["fields"] == [
        {"field": "firstName", "message": "Укажите имя."},
        {"field": "lastName", "message": "Укажите фамилию."},
        {"field": "phone", "message": "Проверьте телефон: нужен номер с кодом страны или города."},
        {"field": "email", "message": "Проверьте адрес почты: похоже, в нём опечатка."},
        {"field": "consent", "message": "Без согласия на обработку персональных данных заявку принять нельзя."},
    ]


def test_filled_trap_field_is_silently_ignored(client):
    response = post(client, {**VALID, "website": "spam"})
    assert response.status_code == 200
    assert not Application.objects.exists()


def test_foreign_origin_is_rejected(client):
    assert post(client, VALID, HTTP_ORIGIN="https://evil.example").status_code == 403
    assert post(client, VALID, HTTP_ORIGIN="http://testserver").status_code == 200


def test_corporate_fields_kept_only_for_organizations(client):
    post(client, {**VALID, "applicantType": "corporate", "employeesCount": "8", "timeframe": "осень"})
    post(client, {**VALID, "email": "other@example.ru", "employeesCount": "8"})
    corporate, personal = Application.objects.order_by("pk")
    assert (corporate.employees_count, corporate.timeframe) == ("8", "осень")
    assert personal.employees_count == ""


def test_letter_lists_applicant_and_program(client, seeded, settings):
    settings.SITE_URL = "https://example.com"
    application = Application.objects.get(pk=post(client, VALID).json()["id"])
    assert subject(application) == "Заявка ДПО: Петров Иван — Английское контрактное право"
    body = letter(application)
    assert "Имя и фамилия: Петров Иван" in body
    assert "Узнал(а) о нас: поисковые системы, другое: друзья" in body
    assert "Страница программы: https://example.com/programs/angliyskoe-kontraktnoe-pravo-856421092.html" in body
    assert f"Заявка № {application.pk}" in body


def test_mail_is_sent_and_marked(client, mailing):
    application = Application.objects.get(pk=post(client, VALID).json()["id"])
    send_application_mail(application.pk)
    application.refresh_from_db()
    assert application.mail_status == MailStatus.SENT
    assert mail.outbox[0].to == ["office@example.ru"]
    assert mail.outbox[0].reply_to == ["ivan@example.ru"]


def test_mail_failure_is_recorded(client, mailing):
    application = Application.objects.get(pk=post(client, VALID).json()["id"])
    failing = patch("django.core.mail.EmailMessage.send", side_effect=smtplib.SMTPException("отказ сервера"))
    with failing, pytest.raises(smtplib.SMTPException):
        send_application_mail(application.pk)
    application.refresh_from_db()
    assert application.mail_status == MailStatus.FAILED
    assert application.mail_error == "отказ сервера"


def test_old_applications_are_purged(client, settings):
    settings.APPLICATION_RETENTION_DAYS = 365
    old = post(client, VALID).json()["id"]
    Application.objects.filter(pk=old).update(received_at=timezone.now() - timedelta(days=366))
    fresh = post(client, {**VALID, "email": "fresh@example.ru"}).json()["id"]
    assert purge_expired() == "Удалено заявок старше 365 дней: 1"
    assert list(Application.objects.values_list("pk", flat=True)) == [fresh]


def test_program_options_match_previous_site(client, seeded):
    legacy = json.loads((FIXTURES / "legacy_programs_index.json").read_text(encoding="utf-8"))["programs"]
    options = client.get("/api/catalog/program-options").json()
    assert [[item["id"], item["title"], item["sphere"]] for item in options] == [
        [item["id"], item["title"], item["sphere"]] for item in legacy
    ]
