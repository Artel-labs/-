from dataclasses import dataclass
from typing import Any

from django.apps import apps
from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.urls import reverse, reverse_lazy
from django.utils.text import capfirst


@dataclass(frozen=True)
class Entry:
    model: str
    icon: str


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    icon: str
    entries: tuple[Entry, ...]
    open: bool = True


SECTIONS = (
    Section(
        "applications",
        "Заявки",
        "mail",
        (Entry("applications.Application", "inbox"), Entry("applications.MailRecipient", "forward_to_inbox")),
    ),
    Section(
        "catalog",
        "Каталог программ",
        "menu_book",
        (
            Entry("catalog.Program", "school"),
            Entry("catalog.Sphere", "category"),
            Entry("catalog.Teacher", "co_present"),
        ),
    ),
    Section("analytics", "Аналитика", "insights", (Entry("analytics.Event", "monitoring"),)),
    Section(
        "users",
        "Пользователи",
        "group",
        (Entry("auth.User", "person"), Entry("accounts.TwoFactor", "verified_user")),
    ),
    Section(
        "protection",
        "Защита входа",
        "shield",
        (
            Entry("axes.AccessAttempt", "block"),
            Entry("axes.AccessFailureLog", "error"),
            Entry("axes.AccessLog", "history"),
        ),
        open=False,
    ),
    Section(
        "tasks",
        "Фоновые задачи",
        "settings",
        (
            Entry("django_q.OrmQ", "pending_actions"),
            Entry("django_q.Schedule", "schedule"),
            Entry("django_q.Failure", "report"),
            Entry("django_q.Success", "task_alt"),
        ),
        open=False,
    ),
)


def model_of(entry: Entry) -> type[Model]:
    return apps.get_model(entry.model)


def route(model: type[Model], action: str) -> str:
    return f"admin:{model._meta.app_label}_{model._meta.model_name}_{action}"


def admin_url(model: type[Model], action: str) -> str:
    return reverse(route(model, action))


def title_of(model: type[Model]) -> str:
    return capfirst(str(model._meta.verbose_name_plural))


def can_view(request: HttpRequest, model: type[Model]) -> bool:
    return bool(admin.site.get_model_admin(model).has_view_or_change_permission(request))


def add_url(request: HttpRequest, model: type[Model]) -> str | None:
    return admin_url(model, "add") if admin.site.get_model_admin(model).has_add_permission(request) else None


def sidebar_item(entry: Entry) -> dict[str, Any]:
    model = model_of(entry)
    return {
        "title": title_of(model),
        "icon": entry.icon,
        "link": reverse_lazy(route(model, "changelist")),
        "permission": lambda request: can_view(request, model),
    }


def sidebar_group(section: Section) -> dict[str, Any]:
    return {
        "key": section.key,
        "title": section.title,
        "open": section.open,
        "collapsible": True,
        "items": [sidebar_item(entry) for entry in section.entries],
    }


def sidebar(request: HttpRequest) -> list[dict[str, Any]]:
    return [sidebar_group(section) for section in SECTIONS]


def tile_item(request: HttpRequest, entry: Entry) -> dict[str, Any] | None:
    model = model_of(entry)
    if not can_view(request, model):
        return None
    return {
        "title": title_of(model),
        "icon": entry.icon,
        "url": admin_url(model, "changelist"),
        "add_url": add_url(request, model),
    }


def tile(request: HttpRequest, section: Section) -> dict[str, Any]:
    items = [tile_item(request, entry) for entry in section.entries]
    return {"title": section.title, "icon": section.icon, "items": [item for item in items if item]}


def tiles(request: HttpRequest) -> list[dict[str, Any]]:
    return [found for found in (tile(request, section) for section in SECTIONS) if found["items"]]
