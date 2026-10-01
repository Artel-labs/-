from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from accounts.admins import DEFAULT_ADMIN_LOGIN, UnknownAdminError, reset_admin_password


class Command(BaseCommand):
    help = "Задаёт администратору новый случайный пароль и снимает блокировку входа"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("login", nargs="?", default=DEFAULT_ADMIN_LOGIN)

    def handle(self, *args: Any, **options: Any) -> None:
        login = options["login"]
        try:
            password = reset_admin_password(login)
        except UnknownAdminError as error:
            raise CommandError(f"Администратора с логином {login} нет") from error
        self.stdout.write(f"Логин:  {login}")
        self.stdout.write(f"Пароль: {password}")
        self.stdout.write("Пароль показан один раз — сохраните его.")
