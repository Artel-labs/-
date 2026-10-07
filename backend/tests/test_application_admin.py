from unittest.mock import patch

import pytest

from applications.models import ApplicantType, Application, MailRecipient, MailStatus, Status, Topic
from applications.service import resend
from tests.factories import make_admin
from tests.test_staff_admin import make_staff

pytestmark = pytest.mark.django_db

CHANGELIST = "/admin/applications/application/"
OK = 200
FOUND = 302
BAD = 400
FORBIDDEN = 403
JSON = {"HTTP_ACCEPT": "application/json"}


@pytest.fixture
def application():
    return Application.objects.create(
        first_name="Анна",
        last_name="Иванова",
        phone="+7 495 000 00 00",
        email="anna@example.ru",
        comment="Перезвоните после обеда",
        mail_status=MailStatus.SKIPPED,
    )


@pytest.fixture
def admin_client(client):
    client.force_login(make_admin())
    return client


def status_url(application: Application) -> str:
    return f"{CHANGELIST}{application.pk}/status/"


def card(client, application: Application) -> str:
    response = client.get(f"{CHANGELIST}{application.pk}/change/")
    assert response.status_code == OK
    return str(response.content.decode())


def test_status_saves_at_once_and_answers_json(admin_client, application):
    response = admin_client.post(status_url(application), {"status": Status.DONE}, **JSON)
    assert response.json() == {"status": "done", "label": "Обработана"}
    application.refresh_from_db()
    assert application.status == Status.DONE


def test_status_without_script_returns_to_card(admin_client, application):
    response = admin_client.post(status_url(application), {"status": Status.IN_PROGRESS})
    assert response.status_code == FOUND
    assert response["Location"].endswith(f"{application.pk}/change/")


def test_status_rejects_unknown_value_and_get(admin_client, application):
    assert admin_client.post(status_url(application), {"status": "lost"}, **JSON).status_code == BAD
    assert admin_client.get(status_url(application)).status_code == FORBIDDEN
    application.refresh_from_db()
    assert application.status == Status.NEW


def test_status_needs_change_permission(client, application):
    viewer = make_staff("viewer")
    viewer.groups.clear()
    client.force_login(viewer)
    assert client.post(status_url(application), {"status": Status.DONE}, **JSON).status_code == FORBIDDEN


def test_staff_can_change_status(client, application):
    client.force_login(make_staff())
    assert client.post(status_url(application), {"status": Status.REJECTED}, **JSON).status_code == OK


def test_list_has_status_control_without_inline_save(admin_client, application):
    html = admin_client.get(CHANGELIST).content.decode()
    assert f'data-status-url="{status_url(application)}"' in html
    assert 'name="form-0-status"' not in html
    assert "toplinks" not in html
    assert ">В работу<" in html.replace("\n", "").replace("  ", "")


def test_card_is_compact(admin_client, application):
    html = card(admin_client, application)
    assert "tel:+7 495 000 00 00" in html
    assert "mailto:anna@example.ru" in html
    assert "Перезвоните после обеда" in html
    assert 'name="_save"' not in html
    assert "Должность" not in html
    assert "Отправить ещё раз" in html


def test_card_shows_details_only_when_filled(admin_client, application):
    application.applicant_type = ApplicantType.CORPORATE
    application.company = "ООО Право"
    application.save()
    html = card(admin_client, application)
    assert "Подробнее" in html
    assert "ООО Право" in html


def test_card_hides_resend_when_mail_sent(admin_client, application):
    application.mail_status = MailStatus.SENT
    application.save()
    assert "Отправить ещё раз" not in card(admin_client, application)


def test_resend_without_server_does_not_queue(settings, application):
    settings.EMAIL_HOST = ""
    with patch("applications.delivery.async_task") as queued:
        result = resend([application])
    assert result.queued == 0
    assert list(result.blocked.values()) == [1]
    queued.assert_not_called()


def test_resend_from_card_explains_why_not_sent(admin_client, settings, application):
    settings.EMAIL_HOST = ""
    response = admin_client.post(f"{CHANGELIST}{application.pk}/resend/", follow=True)
    html = response.content.decode()
    assert "Не отправлено (1): Почтовый сервер не настроен" in html
    assert "поставлены в очередь" not in html


def test_mail_line_is_ok_when_ready(admin_client, settings):
    settings.EMAIL_HOST = "smtp.example.ru"
    MailRecipient.objects.create(email="office@example.ru")
    html = admin_client.get(CHANGELIST).content.decode()
    assert "Почта настроена." in html


def test_check_mail_needs_post(admin_client):
    assert admin_client.get(f"{CHANGELIST}check-mail/").status_code == FORBIDDEN


def test_anonymous_card_has_no_contacts(admin_client):
    feedback = Application.objects.create(topic=Topic.FEEDBACK, comment="Спасибо", mail_status=MailStatus.SKIPPED)
    html = card(admin_client, feedback)
    assert "Анонимно" in html
    assert "Обращение анонимное: контактов заявителя нет." in html
    assert "tel:" not in html
    assert "mailto:" not in html
    assert "Анонсы" not in html


def test_card_shows_consent_record(admin_client, application):
    application.consent_at = application.received_at
    application.consent_version = "hse-consent-test"
    application.save()
    html = card(admin_client, application)
    assert "Согласие на обработку ПДн" in html
    assert "текст «hse-consent-test»" in html


def test_admin_marks_ads_consent_withdrawal(admin_client, application):
    application.ads_consent_at = application.received_at
    application.ads_consent_version = "hse-ads-test"
    application.save()
    response = admin_client.post(CHANGELIST, {"action": "withdraw_ads_consent", "_selected_action": [application.pk]})
    assert response.status_code == FOUND
    application.refresh_from_db()
    assert application.ads_consent_withdrawn_at is not None
    assert "отозвано" in card(admin_client, application)
