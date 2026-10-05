from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate

ROLE_SYNC = "accounts.sync_staff_group"
USERS_SECTION = "Пользователи"


class AccountsConfig(AppConfig):
    name = "accounts"
    verbose_name = USERS_SECTION

    def ready(self) -> None:
        from accounts.roles import sync_staff_group

        post_migrate.connect(sync_staff_group, dispatch_uid=ROLE_SYNC)
        apps.get_app_config("auth").verbose_name = USERS_SECTION
