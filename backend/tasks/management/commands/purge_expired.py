from django.core.management.base import BaseCommand

from tasks.retention import purge_all


class Command(BaseCommand):
    help = "Сразу удаляет данные с истёкшим сроком хранения: заявки, аналитику и журнал входов."

    def handle(self, *args: object, **options: object) -> None:
        for line in purge_all():
            self.stdout.write(line)
