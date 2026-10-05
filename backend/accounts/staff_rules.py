from django.contrib.auth.models import AnonymousUser, User

SELF = "Это ваша учётная запись: такое действие с собой выполнить нельзя."
LAST_ADMIN = "Это последний администратор с доступом: сначала назначьте другого администратора."


def is_last_admin(user: User) -> bool:
    if not (user.is_superuser and user.is_active):
        return False
    return not User.objects.filter(is_superuser=True, is_active=True).exclude(pk=user.pk).exists()


def protected_reason(actor: User | AnonymousUser, target: User) -> str | None:
    if actor.pk == target.pk:
        return SELF
    if is_last_admin(target):
        return LAST_ADMIN
    return None
