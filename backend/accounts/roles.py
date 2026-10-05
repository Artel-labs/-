from typing import Any

from django.contrib.auth.models import Group, Permission, User
from django.db import models, transaction
from django.db.models import Q

STAFF_GROUP = "Сотрудник"
EVERYTHING = ("view", "add", "change", "delete")
WORK_ON = ("view", "change", "delete")
LOOK_AT = ("view",)

STAFF_PERMISSIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("applications", "application", WORK_ON),
    ("applications", "mailrecipient", EVERYTHING),
    ("catalog", "program", EVERYTHING),
    ("catalog", "sphere", EVERYTHING),
    ("catalog", "teacher", EVERYTHING),
    ("catalog", "module", EVERYTHING),
    ("catalog", "programteacher", EVERYTHING),
    ("catalog", "programfile", EVERYTHING),
    ("catalog", "faqitem", EVERYTHING),
    ("catalog", "review", EVERYTHING),
    ("analytics", "event", LOOK_AT),
)


class Role(models.TextChoices):
    ADMIN = "admin", "Администратор"
    STAFF = "staff", "Сотрудник"


ROLE_HELP = (
    "Администратор — все разделы, включая пользователей, защиту входа и фоновые задачи. "
    "Сотрудник — заявки, каталог программ и посещаемость."
)


def role_of(user: User) -> Role:
    return Role.ADMIN if user.is_superuser else Role.STAFF


def staff_group() -> Group:
    group, _ = Group.objects.get_or_create(name=STAFF_GROUP)
    return group


def staff_permissions() -> models.QuerySet[Permission]:
    wanted = Q(pk__in=[])
    for app_label, model, actions in STAFF_PERMISSIONS:
        codenames = [f"{action}_{model}" for action in actions]
        wanted |= Q(content_type__app_label=app_label, codename__in=codenames)
    return Permission.objects.filter(wanted)


def sync_staff_group(**kwargs: Any) -> None:
    staff_group().permissions.set(staff_permissions())


@transaction.atomic
def apply_role(user: User, role: str) -> None:
    user.is_staff = True
    user.is_superuser = role == Role.ADMIN
    user.save(update_fields=["is_staff", "is_superuser"])
    user.user_permissions.clear()
    if role == Role.ADMIN:
        user.groups.clear()
    else:
        user.groups.set([staff_group()])
