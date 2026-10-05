import os
from io import BytesIO
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from PIL import Image

from catalog.models import FileKind, Program, ProgramFile, Source
from catalog.presentation.images import cover
from catalog.presentation.media import file_url, media_url
from catalog.presentation.page import files

pytestmark = pytest.mark.django_db

LATER = 60


def picture(color: str) -> bytes:
    output = BytesIO()
    Image.new("RGB", (800, 450), color).save(output, "JPEG")
    return output.getvalue()


def age(root: Path) -> None:
    for path in root.rglob("*.*"):
        stamp = path.stat().st_mtime - LATER
        os.utime(path, (stamp, stamp))


@pytest.fixture
def program(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    fields = {"hse_id": "100", "title": "Договорное право", "type_short": "ПК", "type_title": "ПК"}
    return Program.objects.create(study_format="Очный", source=Source.HSE, **fields)


def test_missing_file_has_plain_url(program):
    assert media_url("programs/none.jpg") == "/media/programs/none.jpg"


def test_existing_file_has_version(program):
    program.image.save("100.jpg", ContentFile(picture("red")))
    stamp = int(os.stat(program.image.path).st_mtime)
    assert file_url(program.image) == f"/media/programs/100.jpg?v={stamp}"


def test_new_cover_gets_new_urls(program, tmp_path):
    program.image.save("100.jpg", ContentFile(picture("red")))
    cover(program)
    age(tmp_path)
    before = cover(program)
    with open(program.image.path, "wb") as target:
        target.write(picture("blue"))
    after = cover(program)
    assert before is not None
    assert after is not None
    assert before.src != after.src
    assert before.srcset != after.srcset
    assert before.webp_srcset != after.webp_srcset


def test_refreshed_pdf_gets_new_url(program, tmp_path):
    document = ProgramFile.objects.create(program=program, kind=FileKind.SCHEDULE, title="Расписание")
    document.file.save("100-schedule.pdf", ContentFile(b"%PDF old"))
    age(tmp_path)
    before = files(program)[0].url
    document.file.delete(save=False)
    document.file.save("100-schedule.pdf", ContentFile(b"%PDF new"))
    after = files(program)[0].url
    assert before.partition("?")[0] == after.partition("?")[0]
    assert before != after
