import re
from io import BytesIO

import pytest
import respx
from django.core.files.base import ContentFile
from django_q.models import OrmQ, Schedule
from httpx import Response
from PIL import Image

from catalog.hse.client import HseClient
from catalog.hse.listing import page_url
from catalog.models import FileKind, Program, ProgramFile, Source, Teacher
from catalog.sync.media import TEACHER_PHOTO_WIDTH
from catalog.sync.runner import run_sync
from catalog.typography import typeset
from tests.factories import make_admin
from tests.hse_helpers import FIXTURES, fixture

pytestmark = pytest.mark.django_db

LISTED = 24
PROGRAM_PAGE = re.compile(r"https://www\.hse\.ru/edu/dpo/(\d+)$")
PDF = b"%PDF-1.4\n%test\n"
BROKEN_PROGRAM = "906651510"


def picture(width: int = 400) -> bytes:
    output = BytesIO()
    Image.new("RGB", (width, width // 2), "navy").save(output, "PNG")
    return output.getvalue()


def program_page(request):
    match = PROGRAM_PAGE.match(str(request.url))
    assert match
    program_id = match.group(1)
    if program_id == BROKEN_PROGRAM:
        return Response(500)
    page = FIXTURES / f"program-{program_id}.html"
    return Response(200, text=page.read_text(encoding="utf-8") if page.exists() else "<html></html>")


@pytest.fixture
def hse():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(page_url(1)).respond(200, text=fixture("listing-page-1.html"))
        mock.get(page_url(2)).respond(200, text=fixture("listing-page-2.html"))
        mock.get(url__regex=PROGRAM_PAGE.pattern).mock(side_effect=program_page)
        mock.get(url__regex=r".*\.pdf$").respond(200, content=PDF, headers={"content-type": "application/pdf"})
        mock.get(url__regex=r".*").respond(200, content=picture(), headers={"content-type": "image/png"})
        yield mock


@pytest.fixture
def sync_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.HSE_REQUEST_DELAY_SECONDS = 0


def program(hse_id: str, **fields) -> Program:
    defaults = {
        "title": f"Программа {hse_id}",
        "type_short": "ПК",
        "type_title": "ПК",
        "study_format": "Очный",
        "source": Source.HSE,
    }
    return Program.objects.create(hse_id=hse_id, **{**defaults, **fields})


def sync():
    with HseClient() as client:
        return run_sync(client, pause=lambda _: None)


def test_new_programs_are_created_with_details(hse, sync_settings):
    report = sync()
    english = Program.objects.get(hse_id="856421092")
    assert len(report.created) == LISTED - 1
    assert english.title == "Английское контрактное право"
    assert english.sphere is not None
    assert english.tax_refund == "6\u00a0500\u00a0рублей"
    assert english.modules.count() == 8
    assert english.image.name.startswith("programs/856421092")
    assert english.files.get(kind=FileKind.PLAN).file.read() == PDF


def test_existing_program_keeps_content_missing_on_hse(hse, sync_settings):
    program("472681893", about="Старое описание", sphere=None, position=7)
    sync()
    updated = Program.objects.get(hse_id="472681893")
    assert updated.about == "Старое описание"
    assert updated.sphere is None
    assert updated.position == 7


def test_locked_program_is_not_touched(hse, sync_settings):
    program("816497962", title="Название из админки", locked=True)
    report = sync()
    assert Program.objects.get(hse_id="816497962").title == "Название из админки"
    assert report.locked == ["Название из админки"]


def test_programs_gone_from_hse_are_hidden(hse, sync_settings):
    program("111", title="Снята с hse.ru")
    program("222", title="Добавлена вручную", source=Source.MANUAL)
    report = sync()
    assert not Program.objects.get(hse_id="111").is_published
    assert Program.objects.get(hse_id="222").is_published
    assert report.hidden == ["Снята с hse.ru"]


def test_broken_page_is_reported_and_others_continue(hse, sync_settings):
    report = sync()
    assert any("500" in problem for problem in report.problems)
    assert Program.objects.count() == LISTED - 1


def test_teacher_photo_is_shrunk(hse, sync_settings):
    sync()
    teacher = Teacher.objects.get(name="Волос Алексей Александрович")
    with Image.open(teacher.photo) as photo:
        assert photo.width == TEACHER_PHOTO_WIDTH
        assert photo.format == "JPEG"


def test_schedule_file_is_refreshed_but_plan_is_kept(hse, sync_settings):
    existing = program("856421092")
    plan = ProgramFile(program=existing, kind=FileKind.PLAN, title="План", source_url="https://www.hse.ru/a.pdf")
    plan.file.save("856421092-plan.pdf", ContentFile(b"%PDF old plan"))
    sync()
    assert existing.files.get(kind=FileKind.PLAN).file.read() == b"%PDF old plan"
    assert existing.files.get(kind=FileKind.SCHEDULE).file.read() == PDF


def test_summary_lists_counts(hse, sync_settings):
    summary = sync().summary()
    assert f"Новых программ: {LISTED - 1}" in summary
    assert "проблем: 1" in summary


def test_daily_schedule_is_installed():
    schedule = Schedule.objects.get(name="Обновление каталога с hse.ru")
    assert schedule.func == "catalog.tasks.sync_catalog"
    assert schedule.schedule_type == Schedule.DAILY


def test_admin_button_queues_sync(client):
    client.force_login(make_admin())
    response = client.post("/admin/catalog/program/sync/")
    assert response.status_code == 302
    assert OrmQ.objects.count() == 1


def test_synced_texts_are_typeset(hse, sync_settings):
    sync()
    english = Program.objects.get(hse_id="856421092")
    assert english.about
    assert typeset(english.about) == english.about
    assert all(typeset(module.title) == module.title for module in english.modules.all())
    assert all(typeset(item.answer) == item.answer for item in english.faq.all())
