from typing import Any

from django import forms
from django.contrib.auth.signals import user_login_failed
from unfold.forms import AuthenticationForm
from unfold.widgets import UnfoldAdminTextInputWidget

from accounts.two_factor import passes

WRONG_CODE = "Неверный код из приложения-аутентификатора."


class TwoFactorLoginForm(AuthenticationForm):
    code = forms.CharField(
        label="Код из приложения",
        required=False,
        max_length=12,
        help_text="Только если включён двухфакторный вход.",
        widget=UnfoldAdminTextInputWidget(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )

    def clean(self) -> dict[str, Any]:
        cleaned: dict[str, Any] = super().clean()
        user = self.get_user()
        if user is not None and not passes(user, cleaned.get("code") or ""):
            user_login_failed.send(
                sender=__name__, credentials={"username": cleaned.get("username")}, request=self.request
            )
            raise forms.ValidationError(WRONG_CODE, code="invalid_code")
        return cleaned


class CodeForm(forms.Form):
    code = forms.CharField(
        label="Код из приложения",
        max_length=12,
        widget=UnfoldAdminTextInputWidget(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )
