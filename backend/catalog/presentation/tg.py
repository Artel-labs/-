import re
from datetime import date

from django.db.models import QuerySet

from catalog.models import Program, Sphere
from catalog.presentation import links
from catalog.presentation.about import about
from catalog.presentation.cards import kind
from catalog.presentation.catalog import catalog_order
from catalog.presentation.dates import notice_is_fresh, start_label
from catalog.presentation.facets import doc_badge, short_format
from catalog.presentation.images import thumb
from catalog.presentation.labels import FILE_LABELS, effective_price
from catalog.presentation.page import price_terms
from catalog.presentation.text import plain_lines
from catalog.schemas import (
    TgCatalogOut,
    TgFaqOut,
    TgFileOut,
    TgModuleOut,
    TgNoticeOut,
    TgProgramOut,
    TgReviewOut,
    TgSphereOut,
    TgTeacherOut,
)
from catalog.teachers import canonical_name

SPHERE_CHIPS = {
    "corporate": "Корпоративное",
    "digital": "Цифровое и ИС",
    "international": "Международное",
    "finance": "Финансы и налоги",
    "language": "Языки",
    "practice": "Практика",
}
DEFAULT_FILE_TITLE = "Документ"
HTTPS = re.compile(r"^https://", re.IGNORECASE)
DOC_FROM_TIP = re.compile(r"[–—]\s*(.+?)\.?$")


def optional(text: str) -> str | None:
    return text or None


def lines(text: str) -> list[str]:
    return plain_lines(text)


def doc_title(tip: str) -> str | None:
    found = DOC_FROM_TIP.search(tip)
    return found.group(1)[:1].upper() + found.group(1)[1:] if found else None


def old_price(program: Program) -> int | None:
    discounted = program.price is not None and program.base_price is not None and program.price < program.base_price
    return program.base_price if discounted else None


def notice(program: Program, today: date) -> TgNoticeOut | None:
    if not program.notice_text or not notice_is_fresh(program.notice_date, today):
        return None
    url = program.notice_url if HTTPS.match(program.notice_url) else None
    return TgNoticeOut(date=program.notice_date or None, text=program.notice_text, url=url)


def files(program: Program) -> list[TgFileOut]:
    return [
        TgFileOut(
            title=FILE_LABELS.get(item.kind) or item.title or DEFAULT_FILE_TITLE,
            size=item.size_label,
            path=item.file.url,
        )
        for item in program.files.all()
        if item.file
    ]


def teachers(program: Program) -> list[TgTeacherOut]:
    return [
        TgTeacherOut(
            name=canonical_name(link.teacher.name),
            about=link.about,
            photo=link.teacher.photo.url if link.teacher.photo else None,
            page=links.safe_hse_url(link.teacher.page_url) or None,
        )
        for link in program.program_teachers.all()
    ]


def modules(program: Program) -> list[TgModuleOut]:
    return [
        TgModuleOut(title=item.title, hours=item.hours, topics=lines(item.topics)) for item in program.modules.all()
    ]


def tg_program(program: Program, today: date) -> TgProgramOut:
    badge = doc_badge(kind(program))
    found_about = about(program)
    picture = thumb(program)
    cover = program.image.url if program.image else None
    return TgProgramOut(
        id=program.hse_id,
        title=program.title,
        sphere=program.sphere.slug if program.sphere else None,
        badge=badge.label if badge else None,
        doc=doc_title(badge.tip) if badge else None,
        format=optional(short_format(program.study_format)),
        duration=optional(program.duration),
        hours=optional(program.hours),
        start_label=start_label(program.start_date, program.start_month_only, today) or None,
        price=effective_price(program),
        old_price=old_price(program),
        tagline=program.tagline or program.about,
        audience=lines(program.audience),
        results=lines(program.results),
        modules=modules(program),
        cover=cover,
        thumb=picture.src if picture else cover,
        pay=links.pay_url(program.hse_id) or None,
        about=program.about,
        lead=found_about.lead or None if found_about and program.about else None,
        about_items=found_about.items or None if found_about else None,
        audience_intro=optional(program.audience_intro),
        advantages=lines(program.advantages),
        language=optional(program.language),
        schedule=optional(program.schedule),
        price_terms=price_terms(program),
        notice=notice(program, today),
        files=files(program),
        teachers=teachers(program),
        feedback=[TgReviewOut(text=item.text, author=item.author) for item in program.reviews.all() if item.text],
        admission_docs=lines(program.admission_documents),
        faq=[TgFaqOut(q=item.question, a=item.answer) for item in program.faq.all()],
    )


def spheres(programs: list[TgProgramOut]) -> list[TgSphereOut]:
    found = [
        TgSphereOut(
            id=sphere.slug,
            title=SPHERE_CHIPS.get(sphere.slug, sphere.title),
            count=sum(1 for program in programs if program.sphere == sphere.slug),
        )
        for sphere in Sphere.objects.order_by("position", "pk")
    ]
    return [sphere for sphere in found if sphere.count]


def tg_catalog(programs: QuerySet[Program], today: date) -> TgCatalogOut:
    ordered = (
        catalog_order(programs)
        .select_related("sphere")
        .prefetch_related("modules", "files", "reviews", "faq", "program_teachers__teacher")
    )
    items = [tg_program(program, today) for program in ordered]
    return TgCatalogOut(programs=items, spheres=spheres(items))
