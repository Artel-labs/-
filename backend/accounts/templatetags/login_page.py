from django import template

from accounts.login_texts import locked_message as login_locked_message

register = template.Library()


@register.simple_tag
def locked_message() -> str:
    return login_locked_message()
