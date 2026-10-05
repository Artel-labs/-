from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, path, reverse

from catalog.sync.state import SyncKind, is_running, start_sync, sync_state

SYNC_LINE = "admin/catalog/sync_state.html"
SYNC_STARTED = "Обновление с hse.ru запущено. Итог появится в строке над списком, страница обновится сама."
SYNC_BUSY = "Обновление с hse.ru уже идёт — дождитесь итога."


class SyncLine:
    sync_kind: SyncKind
    sync_button: str
    list_before_template = SYNC_LINE

    def route(self, action: str) -> str:
        opts = self.model._meta  # type: ignore[attr-defined]
        return f"{opts.app_label}_{opts.model_name}_{action}"

    def sync_patterns(self) -> list[URLPattern]:
        view = self.admin_site.admin_view  # type: ignore[attr-defined]
        return [
            path("sync/", view(self.sync_view), name=self.route("sync")),
            path("sync/status/", view(self.sync_status_view), name=self.route("sync_status")),
        ]

    def sync_context(self) -> dict[str, Any]:
        return {
            "sync": sync_state(self.sync_kind),
            "sync_url": reverse(f"admin:{self.route('sync')}"),
            "sync_status_url": reverse(f"admin:{self.route('sync_status')}"),
            "sync_button": self.sync_button,
        }

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, Any] | None = None) -> HttpResponse:
        context = {**(extra_context or {}), **self.sync_context()}
        response: HttpResponse = super().changelist_view(request, context)  # type: ignore[misc]
        return response

    def sync_view(self, request: HttpRequest) -> HttpResponseRedirect:
        if request.method != "POST" or not self.has_change_permission(request):  # type: ignore[attr-defined]
            raise PermissionDenied
        if start_sync(self.sync_kind):
            messages.success(request, SYNC_STARTED)
        else:
            messages.warning(request, SYNC_BUSY)
        return HttpResponseRedirect(reverse(f"admin:{self.route('changelist')}"))

    def sync_status_view(self, request: HttpRequest) -> JsonResponse:
        if not self.has_view_or_change_permission(request):  # type: ignore[attr-defined]
            raise PermissionDenied
        return JsonResponse({"running": is_running()})
