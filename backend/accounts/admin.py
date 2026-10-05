from django.contrib import admin, messages
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from unfold.admin import ModelAdmin

from accounts import two_factor
from accounts.forms import WRONG_CODE, CodeForm
from accounts.models import TwoFactor
from accounts.staff_admin import StaffAdmin
from accounts.totp import grouped, provisioning_uri

__all__ = ["StaffAdmin", "TwoFactorAdmin"]

SETTINGS_TEMPLATE = "admin/accounts/twofactor/settings.html"
ENABLED = "Двухфакторный вход включён."
DISABLED = "Двухфакторный вход отключён."


def current_user(request: HttpRequest) -> AbstractBaseUser:
    user = request.user
    if not isinstance(user, AbstractBaseUser):
        raise PermissionDenied
    return user


@admin.register(TwoFactor)
class TwoFactorAdmin(ModelAdmin):
    def has_module_permission(self, request: HttpRequest) -> bool:
        return bool(request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return self.has_module_permission(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, object] | None = None) -> HttpResponse:
        if request.method == "POST":
            return self.handle(request)
        return self.page(request, CodeForm())

    def handle(self, request: HttpRequest) -> HttpResponse:
        action = request.POST.get("action")
        if action == "start":
            two_factor.start(current_user(request))
            return HttpResponseRedirect(request.path)
        form = CodeForm(request.POST)
        code = form.data.get("code", "")
        user = current_user(request)
        done = two_factor.confirm(user, code) if action == "confirm" else two_factor.disable(user, code)
        if done:
            messages.success(request, ENABLED if action == "confirm" else DISABLED)
            return HttpResponseRedirect(request.path)
        form.is_valid()
        form.add_error("code", WRONG_CODE)
        return self.page(request, form)

    def page(self, request: HttpRequest, form: CodeForm) -> TemplateResponse:
        user = current_user(request)
        device = two_factor.device_of(user)
        context = {
            **self.admin_site.each_context(request),
            "title": "Двухфакторный вход",
            "opts": self.model._meta,
            "form": form,
            "device": device,
            "enabled": bool(device and device.enabled),
            "secret_grouped": grouped(device.secret) if device else "",
            "uri": provisioning_uri(device.secret, user.get_username()) if device else "",
        }
        return TemplateResponse(request, SETTINGS_TEMPLATE, context)
