from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils import timezone
from unfold.admin import ModelAdmin

from analytics.dashboard import context, range_of
from analytics.models import Event
from analytics.summary import summary_for

TEMPLATE = "admin/analytics/event/dashboard.html"


@admin.register(Event)
class EventAdmin(ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, object] | None = None) -> TemplateResponse:
        if not self.has_view_permission(request):
            raise PermissionDenied
        days = range_of(request.GET.get("days"))
        page = {
            **self.admin_site.each_context(request),
            **context(summary_for(days, timezone.now())),
            "title": "Посещаемость",
            "opts": self.model._meta,
            "days": days,
        }
        return TemplateResponse(request, TEMPLATE, page)
