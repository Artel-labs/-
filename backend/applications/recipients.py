from applications.models import MailRecipient


def active_recipients() -> list[MailRecipient]:
    return list(MailRecipient.objects.filter(is_active=True))


def recipients_for(topic: str) -> list[str]:
    return [recipient.email for recipient in active_recipients() if topic in recipient.topics]


def all_recipients() -> list[str]:
    return [recipient.email for recipient in active_recipients()]
