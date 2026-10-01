from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"
    verbose_name = "Пользователи"

    def ready(self) -> None:
        from django.contrib import admin

        from accounts.forms import TwoFactorLoginForm

        admin.site.login_form = TwoFactorLoginForm
        admin.site.login_template = "accounts/login.html"
