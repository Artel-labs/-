from datetime import date

from django.conf import settings

from catalog.models import Program
from catalog.presentation import about, images, links, seo
from catalog.presentation.dates import format_start, notice_is_fresh
from catalog.presentation.labels import CREDENTIALS, FILE_LABELS, UNKNOWN, price_label, type_label
from catalog.presentation.media import file_url
from catalog.presentation.text import plain_lines, plural, typographic_lines
from catalog.schemas import (
    AboutOut,
    AudienceOut,
    CoverOut,
    CredentialOut,
    FactOut,
    FaqOut,
    FileOut,
    ModuleOut,
    NoticeOut,
    ProgramPageOut,
    ReviewOut,
    SiblingOut,
    SiblingsOut,
    TeacherOut,
)
from catalog.teachers import canonical_name
from catalog.typography import squeeze_spaces

ONE_TEACHER = "Преподаватель-практик"
MANY_TEACHERS = "Преподаватели-практики"
NO_SPHERE = "Программа"
TAX_REFUND_NOTE = "можно вернуть налоговым вычетом"


def chips(program: Program) -> list[str]:
    return [chip for chip in (type_label(program), program.study_format, program.duration) if chip]


def facts(program: Program) -> list[FactOut]:
    rows = [
        ("Тип программы", type_label(program)),
        ("Формат", program.study_format or UNKNOWN),
        ("Длительность", program.duration or UNKNOWN),
        ("Объём", program.hours),
        ("Язык", program.language),
        ("График занятий", program.schedule),
        ("Старт", format_start(program.start_date, program.start_month_only) or UNKNOWN),
    ]
    return [FactOut(label=label, value=value) for label, value in rows if value]


def price_terms(program: Program) -> list[str]:
    terms = [f"{program.tax_refund} {TAX_REFUND_NOTE}"] if program.tax_refund else []
    return terms + plain_lines(program.discounts)


def notice(program: Program, today: date) -> NoticeOut | None:
    if not program.notice_text or not notice_is_fresh(program.notice_date, today):
        return None
    return NoticeOut(
        date=program.notice_date,
        text=program.notice_text,
        url=program.notice_url,
        host=links.host_label(program.notice_url),
    )


def about_section(program: Program) -> AboutOut | None:
    found = about.about(program)
    return AboutOut(lead=found.lead, body=found.body, items=found.items) if found else None


def audience(program: Program) -> AudienceOut | None:
    items = typographic_lines(program.audience)
    return AudienceOut(intro=squeeze_spaces(program.audience_intro), items=items) if items else None


def modules(program: Program) -> list[ModuleOut]:
    return [
        ModuleOut(
            title=squeeze_spaces(module.title), hours=squeeze_spaces(module.hours), topics=plain_lines(module.topics)
        )
        for module in program.modules.all()
    ]


def files(program: Program) -> list[FileOut]:
    return [
        FileOut(
            label=FILE_LABELS.get(document.kind) or document.title,
            size=document.size_label,
            url=file_url(document.file),
        )
        for document in program.files.all()
        if document.file
    ]


def teachers(program: Program) -> list[TeacherOut]:
    return [
        TeacherOut(
            name=canonical_name(squeeze_spaces(link.teacher.name)),
            about=squeeze_spaces(link.about),
            page_url=links.safe_hse_url(link.teacher.page_url),
        )
        for link in program.program_teachers.select_related("teacher")
    ]


def reviews(program: Program) -> list[ReviewOut]:
    return [
        ReviewOut(text=squeeze_spaces(review.text), author=squeeze_spaces(review.author))
        for review in program.reviews.all()
        if review.text.strip() and review.author.strip()
    ]


def siblings(program: Program) -> SiblingsOut | None:
    if program.sphere is None:
        return None
    members = list(program.sphere.programs.filter(is_published=True).order_by("position", "title"))
    others = [SiblingOut(title=member.title, path=member.path) for member in members if member.pk != program.pk]
    if not others:
        return None
    return SiblingsOut(
        sphere_title=program.sphere.title,
        count_label=plural(len(members), "программа", "программы", "программ"),
        items=others,
    )


def cover(program: Program) -> CoverOut | None:
    found = images.cover(program)
    return CoverOut(**found.__dict__) if found else None


def credential(program: Program) -> CredentialOut | None:
    found = CREDENTIALS.get(program.type_short)
    return CredentialOut(tag=found.tag, name=found.name, note=found.note) if found else None


def program_page(program: Program, today: date) -> ProgramPageOut:
    site_url = settings.SITE_URL
    module_items = modules(program)
    teacher_items = teachers(program)
    return ProgramPageOut(
        hse_id=program.hse_id,
        title=program.title,
        path=program.path,
        canonical_url=f"{site_url}/{program.path}",
        page_title=seo.page_title(program),
        description=seo.meta_description(program),
        image_url=f"{site_url}{file_url(program.image)}" if program.image else "",
        structured_data=seo.structured_data(program, site_url),
        crumb=program.sphere.title if program.sphere else NO_SPHERE,
        chips=chips(program),
        cover=cover(program),
        notice=notice(program, today),
        about=about_section(program),
        audience=audience(program),
        results=typographic_lines(program.results),
        advantages=plain_lines(program.advantages),
        modules=module_items,
        modules_label=plural(len(module_items), "модуль", "модуля", "модулей"),
        files=files(program),
        teachers_heading=ONE_TEACHER if len(teacher_items) == 1 else MANY_TEACHERS,
        teachers=teacher_items,
        reviews=reviews(program),
        admission_documents=plain_lines(program.admission_documents),
        faq=[FaqOut(question=item.question, answer=item.answer) for item in program.faq.all()],
        siblings=siblings(program),
        price=price_label(program),
        price_terms=price_terms(program),
        facts=facts(program),
        pay_url=links.pay_url(program.hse_id),
        hse_url=links.safe_hse_url(program.hse_url),
        credential=credential(program),
    )
