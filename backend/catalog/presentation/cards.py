from datetime import date

from catalog.branches import branch_titles
from catalog.models import Program
from catalog.presentation import images
from catalog.presentation.dates import moscow_millis, start_label
from catalog.presentation.facets import doc_badge, duration_facet, format_facet, format_tip, short_format
from catalog.presentation.labels import price_label
from catalog.presentation.text import plain_lines
from catalog.schemas import CardOut, CompareOut, TagOut, ThumbOut
from catalog.teachers import shown_name
from catalog.typography import plain_spaces, squeeze_spaces

OTHER_SPHERE = "other"
LIST_SEPARATOR = " · "
PLAIN_TAG = "tag"
DOC_TAG = "tag tag-doc"
DURATION_TAG = "tag tag-dur"


def kind(program: Program) -> str:
    return program.type_short or program.type_title


def tag(tag_kind: str, text: str, tip: str = "") -> TagOut:
    return TagOut(kind=tag_kind, text=text, tip=tip)


def tags(program: Program) -> list[TagOut]:
    found = []
    if program.study_format:
        found.append(tag(PLAIN_TAG, short_format(program.study_format), format_tip(program.study_format)))
    badge = doc_badge(kind(program))
    if badge:
        found.append(tag(DOC_TAG, badge.label, badge.tip))
    if program.duration:
        found.append(tag(DURATION_TAG, program.duration))
    return found


def search_text(program: Program, start: str) -> str:
    words = [program.title, kind(program), program.study_format, program.duration, start, *branch_titles(program.title)]
    return plain_spaces(" ".join(word for word in words if word)).lower()


def module_titles(program: Program) -> list[str]:
    titles = (squeeze_spaces(module.title) for module in program.modules.all())
    return [title for title in titles if title]


def teacher_names(program: Program) -> list[str]:
    return [shown_name(link.teacher.name) for link in program.program_teachers.all()]


def compare(program: Program, start: str) -> CompareOut:
    return CompareOut(
        format=short_format(program.study_format) or format_facet(program.study_format).label,
        duration=program.duration,
        start=start,
        modules=LIST_SEPARATOR.join(module_titles(program)),
        teachers=LIST_SEPARATOR.join(teacher_names(program)),
        audience=LIST_SEPARATOR.join(plain_lines(program.audience)),
    )


def thumb(program: Program) -> ThumbOut | None:
    found = images.thumb(program)
    return ThumbOut(src=found.src, webp=found.webp, alt=found.alt) if found else None


def card(program: Program, today: date) -> CardOut:
    start = start_label(program.start_date, program.start_month_only, today)
    return CardOut(
        hse_id=program.hse_id,
        title=program.title,
        path=program.path,
        type_short=kind(program),
        format=format_facet(program.study_format).value,
        sphere=program.sphere.slug if program.sphere else OTHER_SPHERE,
        sphere_title=program.sphere.title if program.sphere else "",
        duration=duration_facet(program.duration).value,
        price_sort=program.base_price or 0,
        start_sort=moscow_millis(program.start_date) if program.start_date else 0,
        title_sort=plain_spaces(program.title).lower(),
        search=search_text(program, start),
        thumb=thumb(program),
        tags=tags(program),
        start=start,
        price=price_label(program),
        compare=compare(program, start),
    )
