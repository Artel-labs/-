import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from catalog.legacy import import_catalog
from catalog.models import Program

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"
SEED_FILE = "catalog.json"


class Command(BaseCommand):
    help = "Заполняет пустой каталог данными прежнего сайта"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--source", type=Path, default=SEED_DIR)

    def handle(self, *args: Any, **options: Any) -> None:
        if Program.objects.exists():
            self.stdout.write("Каталог уже заполнен — начальные данные не загружаем.")
            return
        root = options["source"]
        data = json.loads((root / SEED_FILE).read_text(encoding="utf-8"))
        count = import_catalog(data, root)
        self.stdout.write(f"Загружено программ: {count}")
