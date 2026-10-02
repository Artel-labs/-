from typing import Any

from django import forms
from unfold.widgets import UnfoldAdminTextInputWidget

WRONG_CODE = "Неверный код из приложения-аутентификатора."


class CodeForm(forms.Form):
    code = forms.CharField(
        label="Код из приложения",
        max_length=12,
        widget=UnfoldAdminTextInputWidget(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )


class LoginCodeForm(CodeForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["code"].widget.attrs["autofocus"] = ""
