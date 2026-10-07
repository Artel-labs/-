import pytest
from django.core.exceptions import ValidationError

from applications.mail_state import mail_state
from applications.models import MailRecipient, Topic
from applications.recipient_domain import OUTSIDE_DOMAIN, in_allowed_domain
from applications.recipients import all_recipients, recipients_for
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

ADD_URL = "/admin/applications/mailrecipient/add/"


@pytest.fixture
def admin_client(client):
    client.force_login(make_admin())
    return client


@pytest.mark.parametrize(
    ("email", "allowed"),
    [
        ("office@hse.ru", True),
        (" Office@HSE.RU ", True),
        ("office@edu.hse.ru", False),
        ("office@evilhse.ru", False),
        ("office@hse.ru.example.com", False),
        ("office@gmail.com", False),
    ],
)
def test_only_hse_addresses_are_allowed(email, allowed):
    assert in_allowed_domain(email) is allowed


def test_recipient_outside_domain_is_not_saved_by_validation():
    with pytest.raises(ValidationError, match=OUTSIDE_DOMAIN):
        MailRecipient(email="office@gmail.com").full_clean()


def test_admin_refuses_recipient_outside_domain(admin_client):
    data = {"email": "office@gmail.com", "note": "", "topics": [Topic.PROGRAM], "is_active": "on"}
    response = admin_client.post(ADD_URL, data)
    assert OUTSIDE_DOMAIN in response.content.decode()
    assert not MailRecipient.objects.exists()


def test_admin_saves_hse_recipient(admin_client):
    data = {"email": "office@hse.ru", "note": "", "topics": [Topic.PROGRAM], "is_active": "on"}
    admin_client.post(ADD_URL, data)
    assert list(MailRecipient.objects.values_list("email", flat=True)) == ["office@hse.ru"]


def test_old_recipient_outside_domain_gets_no_mail(settings):
    settings.EMAIL_HOST = "smtp.example.ru"
    MailRecipient.objects.create(email="office@hse.ru")
    MailRecipient.objects.create(email="old@gmail.com")
    assert all_recipients() == ["office@hse.ru"]
    assert recipients_for(Topic.PROGRAM) == ["office@hse.ru"]
    state = mail_state()
    assert not state.ok
    assert "old@gmail.com" in state.headline
