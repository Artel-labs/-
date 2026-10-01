from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from accounts.two_factor import reset


class Command(BaseCommand):
    help = "Отключает двухфакторный вход пользователя (например, если потерян телефон)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("login")

    def handle(self, *args: object, **options: str) -> None:
        user = get_user_model().objects.filter(username=options["login"]).first()
        if user is None:
            raise CommandError(f"Пользователь {options['login']} не найден.")
        if reset(user):
            self.stdout.write(f"Двухфакторный вход для {options['login']} отключён.")
        else:
            self.stdout.write(f"У {options['login']} двухфакторный вход не был включён.")
