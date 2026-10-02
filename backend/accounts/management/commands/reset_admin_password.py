from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from accounts.admins import UnknownAdminError, admin_logins, reset_admin_password
from accounts.logins import LoginChoice, chosen_login

ADMINS = LoginChoice(
    script="./scripts/reset-admin-password.sh",
    nobody="Администраторов нет. Создайте: ./scripts/create-admin.sh",
    listed="Администраторов несколько",
)


class Command(BaseCommand):
    help = "Задаёт администратору новый случайный пароль и снимает блокировку входа"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("login", nargs="?")

    def handle(self, *args: Any, **options: Any) -> None:
        logins = admin_logins()
        login = chosen_login(options["login"], logins, ADMINS)
        try:
            password = reset_admin_password(login)
        except UnknownAdminError as error:
            raise CommandError(f"Администратора с логином {login} нет. Администраторы: {', '.join(logins)}") from error
        self.stdout.write(f"Логин:  {login}")
        self.stdout.write(f"Пароль: {password}")
        self.stdout.write("Пароль показан один раз — сохраните его.")
