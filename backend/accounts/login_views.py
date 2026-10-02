from typing import Any

from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_lockout_response
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from accounts import two_factor
from accounts.forms import WRONG_CODE, LoginCodeForm
from accounts.pending_login import PendingLogin, forget, pending, pending_user, remember

CODE_TEMPLATE = "accounts/login_code.html"


class PasswordStepView(LoginView):
    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        forget(self.request)
        user = form.get_user()
        if not two_factor.is_enabled(user):
            return super().form_valid(form)
        remember(self.request, user, getattr(user, "backend", ""), self.get_success_url())
        return HttpResponseRedirect(reverse("admin:login_code"))


class CodeStepView(FormView):
    form_class = LoginCodeForm
    template_name = CODE_TEMPLATE
    login: PendingLogin
    user: User

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        login = pending(request)
        user = pending_user(login) if login else None
        if login is None or user is None:
            return redirect("admin:login")
        self.login, self.user = login, user
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return {**super().get_context_data(**kwargs), "login_name": self.user.get_username()}

    def form_valid(self, form: LoginCodeForm) -> HttpResponse:
        credentials = {"username": self.user.get_username()}
        if not AxesProxyHandler.is_allowed(self.request, credentials):
            forget(self.request)
            locked: HttpResponse = get_lockout_response(self.request, credentials=credentials)
            return locked
        if self.accepts(form.cleaned_data["code"]):
            forget(self.request)
            auth_login(self.request, self.user, backend=self.login.backend)
            return HttpResponseRedirect(self.login.redirect_to)
        user_login_failed.send(sender=__name__, credentials=credentials, request=self.request)
        form.add_error("code", WRONG_CODE)
        return self.form_invalid(form)

    def accepts(self, code: str) -> bool:
        device = two_factor.device_of(self.user)
        return bool(device and device.enabled and two_factor.accept_code(device, code))
