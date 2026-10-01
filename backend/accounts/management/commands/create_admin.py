from typing import Any

from django.core.management.base import BaseCommand

from accounts.admins import DEFAULT_ADMIN_LOGIN, admin_exists, create_first_admin


class Command(BaseCommand):
    help = "Создаёт первого администратора со случайным паролем, если администратора ещё нет"

    def handle(self, *args: Any, **options: Any) -> None:
        if admin_exists():
            self.stdout.write("Администратор уже есть — новый не создаём.")
            return
        password = create_first_admin()
        self.stdout.write(f"Логин:  {DEFAULT_ADMIN_LOGIN}")
        self.stdout.write(f"Пароль: {password}")
        self.stdout.write("Пароль показан один раз — сохраните его. Сменить: ./scripts/reset-admin-password.sh")
