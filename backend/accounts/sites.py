from typing import Any

from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.urls import URLPattern, path, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from unfold.sites import UnfoldAdminSite

from accounts.login_views import CodeStepView, PasswordStepView

CODE_TITLE = "Подтверждение входа"
LOGIN_TEMPLATE = "accounts/login.html"


class DpoAdminSite(UnfoldAdminSite):
    login_template = LOGIN_TEMPLATE

    def extra_urls(self) -> list[URLPattern]:
        return [path("login/code/", self.login_code, name="login_code")]

    def step_context(self, request: HttpRequest, title: str) -> dict[str, Any]:
        return {
            **self.each_context(request),
            "title": title,
            "subtitle": None,
            "app_path": request.get_full_path(),
            "username": request.user.get_username(),
        }

    @method_decorator(never_cache)
    @method_decorator(login_not_required)
    def login(self, request: HttpRequest, extra_context: dict[str, Any] | None = None) -> HttpResponseBase:
        if request.method == "GET" and self.has_permission(request):
            return HttpResponseRedirect(reverse("admin:index", current_app=self.name))
        request.current_app = self.name
        view = PasswordStepView.as_view(
            extra_context={**self.step_context(request, _("Log in")), **(extra_context or {})},
            authentication_form=self.login_form,
            template_name=self.login_template or "admin/login.html",
        )
        return view(request)

    @method_decorator(never_cache)
    @method_decorator(login_not_required)
    def login_code(self, request: HttpRequest) -> HttpResponseBase:
        request.current_app = self.name
        return CodeStepView.as_view(extra_context=self.step_context(request, CODE_TITLE))(request)
