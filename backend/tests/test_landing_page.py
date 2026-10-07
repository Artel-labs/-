import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from catalog.landing_schemas import LandingOut
from catalog.models import TOP_PLACES, Program, Teacher
from catalog.presentation.landing.page import landing_page
from catalog.presentation.page import program_page
from tests.media import unversioned
from tests.typography import untypeset

pytestmark = pytest.mark.django_db

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_landing.json").read_text(encoding="utf-8"))
LEGACY_DAY = date(2026, 10, 1)
HIDDEN_TEACHER_PROGRAM = "1029651795"
HIDDEN_TEACHER = "Духовная Татьяна Сергеевна"
HIDDEN_ON_LANDING = (HIDDEN_TEACHER,)
LEGACY_CATALOG = "Каталог программ.html"
LEGACY_IMAGES = "images/"
MEDIA_URL = "/media/"
TILE_FIELDS_REMOVED = ("rank", "tagline", "price")
SPHERE_FIELDS_REMOVED = ("index",)
STEP_COLORS = {
    1: "--step-bg:#1658DA;--step-ink:#FFFFFF;--step-soft:rgba(255,255,255,.86)",
    2: "--step-bg:#0B2A69;--step-ink:#FFFFFF;--step-soft:rgba(255,255,255,.86)",
    3: "--step-bg:#E6D4BF;--step-ink:#211E1B;--step-soft:#5A5248",
    4: "--step-bg:#CEDFFD;--step-ink:#211E1B;--step-soft:#48423A",
}


def site_href(href: str) -> str:
    if href.startswith(LEGACY_CATALOG):
        return "/catalog" + href.removeprefix(LEGACY_CATALOG)
    if href.startswith("programs/"):
        return f"/{href}"
    if href.startswith(LEGACY_IMAGES):
        return MEDIA_URL + href.removeprefix(LEGACY_IMAGES)
    return href


@pytest.fixture
def page(settings, tmp_path) -> LandingOut:
    settings.MEDIA_ROOT = tmp_path
    call_command("seed_catalog", stdout=StringIO())
    return landing_page(Program.objects.filter(is_published=True), LEGACY_DAY)


def test_landing_has_no_spheres_dropdown_menu(page):
    assert "menu" not in page.model_dump()


def legacy_sphere(card: dict[str, Any]) -> dict[str, Any]:
    kept = {key: value for key, value in card.items() if key not in SPHERE_FIELDS_REMOVED}
    return {**kept, "href": site_href(card["href"])}


def test_sphere_cards_match_previous_site_without_numbers(page):
    cards = [card.dict() for card in page.spheres]
    assert untypeset(cards) == untypeset([legacy_sphere(card) for card in LEGACY["spheres"]])


def test_sphere_cards_have_no_numbers(page):
    assert all(field not in card.dict() for card in page.spheres for field in SPHERE_FIELDS_REMOVED)


def format_record(row: Any) -> dict[str, Any]:
    doc = row.doc
    return {
        "doc": None if doc is None else [f"images/{doc.file}", doc.ext, str(doc.height), doc.name],
        "band": STEP_COLORS[row.step],
        "index": row.index,
        "title": row.title,
        "tagline": row.tagline,
        "desc": row.desc,
        "facts": row.document,
        "stats": [[stat.key, stat.value] for stat in row.stats],
        "start": row.start,
        "count": row.count,
        "ctas": [[row.cta.href, row.cta.label, "_blank" if row.cta.external else "", row.cta.application]],
    }


NEW_FORMAT_TEXTS = {
    "Повышение квалификации": (
        "",
        "Короткие и интенсивные программы для специалистов, кто ценит время и стремится быть в курсе изменений в "
        "законодательстве, осваивать новые компетенции или углубляться в узкую область права без отрыва от основной "
        "работы.",
        "По окончании обучения выдается удостоверение о повышении квалификации.",
    ),
    "Профессиональная переподготовка": (
        "Новый уровень вашей карьеры.",
        "Углубленные программы для тех, кто хочет получить дополнительную квалификацию, расширить профессиональные "
        "возможности или выстроить новую карьерную траекторию. Мы объединили максимум практики и системный подход, "
        "чтобы вы могли уверенно чувствовать себя в выбранной сфере.",
        "По итогам обучения выдается диплом о профессиональной переподготовке.",
    ),
    "Дополнительное образование для взрослых": (
        "Юридическая грамотность без лишних сложностей.",
        "Курсы и отдельные модули созданы для тех, кому нужны прикладные знания без получения новой квалификации. "
        "Изучайте право точечно и эффективно.",
        "Свидетельство об обучении (при успешном освоении программы).",
    ),
    "Второе высшее образование": (
        "Получите качественное юридическое образование, которое станет вашим главным конкурентным преимуществом.",
        "Фундаментальная программа бакалавриата «Юриспруденция: правовое регулирование бизнеса». Можно выбрать "
        "профиль подготовки: корпоративный юрист или специалист в сфере строительства, недвижимости, финансового и "
        "налогового права.",
        "По итогам обучения выдается диплом о высшем образовании.",
    ),
}


def with_new_texts(row: dict[str, Any]) -> dict[str, Any]:
    tagline, desc, document = NEW_FORMAT_TEXTS[row["title"]]
    ctas = [[site_href(cta[0]), *cta[1:]] for cta in row["ctas"]]
    return {**row, "tagline": tagline, "desc": desc, "facts": document, "ctas": ctas}


def test_formats_match_previous_site_with_new_texts(page):
    legacy = [with_new_texts(row) for row in LEGACY["formats"]]
    assert untypeset([format_record(row) for row in page.formats]) == untypeset(legacy)


def legacy_teacher(record: dict[str, Any]) -> dict[str, Any]:
    payload = record["payload"]
    programs = [{"t": item["t"], "h": site_href(item["h"])} for item in payload["programs"]]
    photo = record["photo"]
    return {
        **record,
        "payload": {**payload, "programs": programs},
        "photo": None if photo is None else [site_href(photo[0]), site_href(photo[1]), photo[2]],
    }


def teacher_record(card: Any) -> dict[str, Any]:
    photo = card.photo
    return {
        "payload": json.loads(card.payload),
        "initials": card.initials,
        "photo": None if photo is None else [photo.src, photo.webp, photo.alt],
        "name": card.name,
        "link": card.page,
        "more": [card.more_label, card.count],
        "desc": card.about,
    }


def test_teachers_match_previous_site(page):
    assert untypeset(unversioned([teacher_record(card) for card in page.teachers])) == untypeset(
        [legacy_teacher(record) for record in LEGACY["teachers"] if record["name"] not in HIDDEN_ON_LANDING]
    )


def test_hidden_teacher_is_not_on_landing(page):
    assert all(HIDDEN_TEACHER not in card.payload for card in page.teachers)


def test_hidden_teacher_stays_on_program_page(page):
    program = Program.objects.get(hse_id=HIDDEN_TEACHER_PROGRAM)
    names = [teacher.name for teacher in program_page(program, LEGACY_DAY).teachers]
    assert HIDDEN_TEACHER in names


def test_seed_marks_hidden_teacher(page):
    assert list(Teacher.objects.filter(show_on_landing=False).values_list("name", flat=True)) == [HIDDEN_TEACHER]


def test_flag_hides_any_teacher_from_landing(page):
    shown = json.loads(page.teachers[0].payload)["name"]
    Teacher.objects.filter(name=shown).update(show_on_landing=False)
    names = [card.name for card in landing_page(Program.objects.filter(is_published=True), LEGACY_DAY).teachers]
    assert shown not in names
    assert len(names) == len(page.teachers) - 1


def test_starts_strip_matches_previous_site(page):
    starts = [[item.path, item.label, item.big, item.is_month, item.small, item.title] for item in page.starts]
    assert untypeset(starts) == untypeset([[site_href(item[0]), *item[1:]] for item in LEGACY["starts"]])


def test_reviews_match_previous_site(page):
    reviews = [[item.text, item.author, item.path, item.program] for item in page.reviews]
    assert untypeset(reviews) == untypeset(
        [[text, author, site_href(href), title] for text, author, href, title in LEGACY["reviews"]]
    )


def top_record(item: Any) -> dict[str, str]:
    record = {
        "image": item.image,
        "imageWebp": item.image_webp,
        "id": item.id,
        "start": item.start,
        "title": item.title,
        "kind": item.kind,
        "format": item.format,
        "formatTip": item.format_tip,
        "doc": item.doc,
        "docTip": item.doc_tip,
        "duration": item.duration,
        "href": item.path,
    }
    return {key: value for key, value in record.items() if value or key not in ("image", "imageWebp")}


def test_top_programs_match_previous_site(page):
    legacy = [
        {
            key: site_href(value) if key in ("image", "imageWebp", "href") else value
            for key, value in item.items()
            if key not in TILE_FIELDS_REMOVED
        }
        for item in LEGACY["top"][:TOP_PLACES]
    ]
    assert untypeset(unversioned([top_record(item) for item in page.top])) == untypeset(legacy)


def test_landing_endpoint(client, page):
    response = client.get("/api/catalog/landing")
    assert response.status_code == 200
    assert len(response.json()["teachers"]) == len(LEGACY["teachers"]) - len(HIDDEN_ON_LANDING)


def test_landing_texts_follow_brandbook_typography(page):
    starts = [row.start for row in page.formats if row.start]
    assert starts
    assert all(start.startswith("Ближайший старт — ") for start in starts)
    assert all(" – " not in row.desc for row in page.formats)
