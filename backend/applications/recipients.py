from applications.models import MailRecipient
from applications.recipient_domain import in_allowed_domain


def active_recipients() -> list[MailRecipient]:
    return [
        recipient for recipient in MailRecipient.objects.filter(is_active=True) if in_allowed_domain(recipient.email)
    ]


def outside_domain() -> list[str]:
    return [
        email
        for email in MailRecipient.objects.filter(is_active=True).values_list("email", flat=True)
        if not in_allowed_domain(email)
    ]


def recipients_for(topic: str) -> list[str]:
    return [recipient.email for recipient in active_recipients() if topic in recipient.topics]


def all_recipients() -> list[str]:
    return [recipient.email for recipient in active_recipients()]
