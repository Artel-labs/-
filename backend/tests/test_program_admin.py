from datetime import timedelta

import pytest
from django.utils import timezone
from django_q.models import OrmQ, Task

from catalog.hse.listing import ListedProgram
from catalog.models import Module, Program, Source
from catalog.publishing import remember_visibility
from catalog.sync.fields import apply_listing
from catalog.sync.state import SYNC_FUNCTION
from tests.factories import make_admin

pytestmark = pytest.mark.django_db

PROGRAMS = "/admin/catalog/program/"
OK = 200
FOUND = 302
FORBIDDEN = 403
TITLE_INPUT = 'name="title"'
PUBLISHED_INPUT = 'name="is_published"'


@pytest.fixture
def admin_client(client):
    client.force_login(make_admin())
    return client


def make_program(**fields) -> Program:
    defaults = {"hse_id": "100", "title": "Договорное право", "type_short": "ПК", "type_title": "ПК"}
    return Program.objects.create(**{"study_format": "Очный", "source": Source.HSE, **defaults, **fields})


def card(client, program: Program) -> str:
    response = client.get(f"{PROGRAMS}{program.pk}/change/")
    assert response.status_code == OK
    return str(response.content.decode())


def listed(program: Program) -> ListedProgram:
    return ListedProgram(
        program.hse_id, program.title, "https://hse.ru/p", "ПК", "ПК", "Очный", "", None, False, None, None
    )


def finished(success: bool, result: str) -> Task:
    now = timezone.now()
    return Task.objects.create(
        id=f"t{int(success)}",
        name="sync",
        func=SYNC_FUNCTION,
        started=now - timedelta(minutes=2),
        stopped=now,
        success=success,
        result=result,
    )


def test_card_has_four_tabs(admin_client):
    html = card(admin_client, make_program())
    for key in ("main", "terms", "text", "content"):
        assert f'data-dpo-tab="{key}"' in html


def test_hse_program_is_read_only_but_visibility_editable(admin_client):
    html = card(admin_client, make_program())
    assert TITLE_INPUT not in html
    assert PUBLISHED_INPUT in html
    assert "Править вручную" in html


def test_hse_program_modules_are_read_only(admin_client):
    program = make_program()
    Module.objects.create(program=program, title="Вводный модуль", position=0)
    assert 'name="modules-0-title"' not in card(admin_client, program)


def test_manual_program_is_editable_without_banner(admin_client):
    html = card(admin_client, make_program(source=Source.MANUAL))
    assert TITLE_INPUT in html
    assert "Править вручную" not in html


def test_manual_edit_asks_then_unlocks(admin_client):
    program = make_program()
    url = f"{PROGRAMS}{program.pk}/manual/"
    assert "Править вручную?" in admin_client.get(url).content.decode()
    assert admin_client.post(url).status_code == FOUND
    program.refresh_from_db()
    assert program.locked
    html = card(admin_client, program)
    assert TITLE_INPUT in html
    assert "Вернуть обновление с hse.ru" in html


def test_follow_hse_locks_fields_again(admin_client):
    program = make_program(locked=True)
    admin_client.post(f"{PROGRAMS}{program.pk}/follow-hse/")
    program.refresh_from_db()
    assert not program.locked


def test_manual_switch_only_for_hse_programs(admin_client):
    program = make_program(source=Source.MANUAL)
    assert admin_client.post(f"{PROGRAMS}{program.pk}/manual/").status_code == FORBIDDEN


def test_hidden_by_hand_survives_sync():
    program = make_program(is_published=False)
    remember_visibility(program, visibility_changed=True)
    program.save()
    apply_listing(program, listed(program), {})
    assert not program.is_published


def test_auto_hidden_program_returns_after_sync():
    program = make_program(is_published=False)
    apply_listing(program, listed(program), {})
    assert program.is_published


def test_sync_line_before_first_run(admin_client):
    assert "Каталог ещё не обновлялся с hse.ru." in admin_client.get(PROGRAMS).content.decode()


def test_sync_button_queues_once(admin_client):
    admin_client.post(f"{PROGRAMS}sync/")
    response = admin_client.post(f"{PROGRAMS}sync/", follow=True)
    assert OrmQ.objects.count() == 1
    html = response.content.decode()
    assert "уже идёт" in html
    assert "Идёт обновление каталога с hse.ru" in html
    assert admin_client.get(f"{PROGRAMS}sync/status/").json() == {"running": True}


def test_sync_needs_post(admin_client):
    assert admin_client.get(f"{PROGRAMS}sync/").status_code == FORBIDDEN


def test_sync_line_reports_problems(admin_client):
    finished(True, "Новых программ: 0; обновлено: 3; проблем: 2\n— обложка «А»: timeout")
    html = admin_client.get(PROGRAMS).content.decode()
    assert "с проблемами (2)" in html
    assert "обложка «А»: timeout" in html


def test_sync_line_reports_failure(admin_client):
    finished(False, "[Errno 111] Connection refused : Traceback (most recent call last):\n  File ...")
    html = admin_client.get(PROGRAMS).content.decode()
    assert "— не удалось." in html
    assert "Причина: [Errno 111] Connection refused<" in html.replace("\n", "").replace("  ", "")
