from typing import Any

from axes.models import AccessAttempt, AccessFailureLog, AccessLog
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from unfold.admin import ModelAdmin
from unfold.decorators import display

from core.admin_tools import ViewOnly, take_over
from protection.lockout import locked_attempts, status, unlock
from protection.login_journal import JOURNAL_LIMIT, PERIODS, Outcome, entries
from protection.models import Lockout, LoginJournal
from protection.user_agents import short_agent

JOURNAL_TEMPLATE = "admin/protection/loginjournal/journal.html"
LOCKED = "locked"
FAILED_ONLY = "failed"

take_over(AccessAttempt, AccessLog, AccessFailureLog)


class LockoutStateFilter(admin.SimpleListFilter):
    title = "Состояние"
    parameter_name = "state"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [(LOCKED, "Заблокированы"), (FAILED_ONLY, "Только ошибки")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Lockout]) -> QuerySet[Lockout]:
        locked = locked_attempts().values("pk")
        if self.value() == LOCKED:
            return queryset.filter(pk__in=locked)
        if self.value() == FAILED_ONLY:
            return queryset.exclude(pk__in=locked)
        return queryset


@admin.register(Lockout)
class LockoutAdmin(ViewOnly, ModelAdmin):
    list_display = ["login", "ip_address", "browser", "failures", "state", "attempt_time"]
    list_display_links = ["login"]
    list_filter = [LockoutStateFilter]
    search_fields = ["username", "ip_address"]
    ordering = ["-attempt_time"]
    actions = ["unlock_selected"]
    fields = ["login", "ip_address", "browser", "failures", "state", "attempt_time"]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @display(description="Логин", ordering="username")
    def login(self, attempt: Lockout) -> str:
        return attempt.username or "—"

    @display(description="Браузер")
    def browser(self, attempt: Lockout) -> str:
        return short_agent(attempt.user_agent)

    @display(description="Ошибок", ordering="failures_since_start")
    def failures(self, attempt: Lockout) -> int:
        return int(attempt.failures_since_start)

    @display(description="Состояние")
    def state(self, attempt: Lockout) -> str:
        return status(attempt)

    @admin.action(description="Снять блокировку")
    def unlock_selected(self, request: HttpRequest, queryset: QuerySet[Lockout]) -> None:
        attempts = list(queryset)
        for attempt in attempts:
            unlock(attempt.username or "", attempt.ip_address)
        self.message_user(request, f"Блокировка снята: {len(attempts)}.")


@admin.register(LoginJournal)
class LoginJournalAdmin(ViewOnly, ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, Any] | None = None) -> HttpResponse:
        if not self.has_view_permission(request):
            raise PermissionDenied
        outcome = request.GET.get("outcome", "")
        days = request.GET.get("days", "")
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": self.model._meta.verbose_name_plural,
            "rows": entries(outcome if outcome in Outcome.values else None, days),
            "outcomes": Outcome.choices,
            "periods": PERIODS,
            "outcome": outcome,
            "days": days,
            "limit": JOURNAL_LIMIT,
        }
        return TemplateResponse(request, JOURNAL_TEMPLATE, context)
