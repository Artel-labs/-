import importlib
from io import StringIO

import pytest
from django.apps import apps
from django.core.management import call_command

from catalog.models import FileKind, Program, Review, Sphere, Teacher
from catalog.spheres import SPHERE_RULES

pytestmark = pytest.mark.django_db

SEED_PROGRAMS = 34
LOCKED_PROGRAMS = 9
UNASSIGNED_TITLE = "Право и\u00a0обществознание"


@pytest.fixture
def seeded(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    output = StringIO()
    call_command("seed_catalog", stdout=output)
    return output.getvalue()


def test_seed_loads_whole_catalog(seeded):
    assert f"Загружено программ: {SEED_PROGRAMS}" in seeded
    assert Program.objects.count() == SEED_PROGRAMS
    assert Program.objects.filter(locked=True).count() == LOCKED_PROGRAMS
    assert Sphere.objects.count() == len(SPHERE_RULES)
    assert list(Program.objects.filter(sphere=None).values_list("title", flat=True)) == [UNASSIGNED_TITLE]


def test_seed_keeps_program_details(seeded):
    program = Program.objects.get(hse_id="856421092")
    assert program.title == "Английское контрактное право"
    assert program.price == 50000
    assert program.sphere is not None
    assert program.sphere.slug == "corporate"
    assert program.modules.count() == 8
    assert program.files.filter(kind=FileKind.PLAN).get().file.size > 0
    assert program.program_teachers.get().teacher.name == "Волос Алексей Александрович"


def test_seed_attaches_media(seeded):
    assert Program.objects.exclude(image="").count() == 32
    assert Teacher.objects.exclude(photo="").count() == 87


def test_seed_runs_once(seeded):
    output = StringIO()
    call_command("seed_catalog", stdout=output)
    assert "уже заполнен" in output.getvalue()
    assert Program.objects.count() == SEED_PROGRAMS


def test_seed_texts_are_typeset(seeded):
    review = Review.objects.get(text__contains="Авакян")
    assert "Авакян\u00a0Е.\u200aГ." in review.text


def test_migration_typesets_existing_catalog(seeded):
    Program.objects.filter(title=UNASSIGNED_TITLE).update(about="Курс – в работе")
    importlib.import_module("catalog.migrations.0004_typeset_catalog").typeset_existing(apps, None)
    assert Program.objects.get(title=UNASSIGNED_TITLE).about == "Курс\u00a0— в\u00a0работе"
