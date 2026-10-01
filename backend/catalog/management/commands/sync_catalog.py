from typing import Any

from django.core.management.base import BaseCommand

from catalog.tasks import sync_catalog


class Command(BaseCommand):
    help = "Обновляет каталог программ с hse.ru"

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(sync_catalog())
