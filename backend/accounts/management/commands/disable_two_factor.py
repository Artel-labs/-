from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from accounts.logins import LoginChoice, chosen_login
from accounts.two_factor import protected_logins, reset

PROTECTED = LoginChoice(
    script="./scripts/disable-two-factor.sh",
    nobody="Двухфакторный вход не включён ни у одного пользователя.",
    listed="Двухфакторный вход включён у нескольких пользователей",
)


class Command(BaseCommand):
    help = "Отключает двухфакторный вход пользователя (например, если потерян телефон)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("login", nargs="?")

    def handle(self, *args: object, **options: str | None) -> None:
        login = chosen_login(options["login"], protected_logins(), PROTECTED)
        user = get_user_model().objects.filter(username=login).first()
        if user is None:
            raise CommandError(f"Пользователь {login} не найден.")
        if reset(user):
            self.stdout.write(f"Двухфакторный вход для {login} отключён.")
        else:
            self.stdout.write(f"У {login} двухфакторный вход не был включён.")
