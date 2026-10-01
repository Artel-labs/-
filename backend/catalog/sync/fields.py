from catalog.hse.details import ProgramDetails
from catalog.hse.listing import ListedProgram
from catalog.models import Program, Source, Sphere
from catalog.spheres import match_sphere


def lines(items: list[str]) -> str:
    return "\n".join(items)


def place_new_program(program: Program, spheres: dict[str, Sphere]) -> None:
    match = match_sphere(program.title)
    if match:
        program.sphere = spheres[match.slug]
        program.position = match.position


def apply_listing(program: Program | None, item: ListedProgram, spheres: dict[str, Sphere]) -> Program:
    is_new = program is None
    program = program or Program(hse_id=item.hse_id)
    program.title = item.title
    program.hse_url = item.url
    program.type_short = item.type_short
    program.type_title = item.type_title
    program.study_format = item.study_format
    program.duration = item.duration
    program.start_date = item.start_date
    program.start_month_only = item.start_month_only
    program.price = item.price
    program.base_price = item.base_price
    program.source = Source.HSE
    program.is_published = True
    if is_new:
        place_new_program(program, spheres)
    return program


def keep_or_replace(current: str, fresh: str) -> str:
    return fresh or current


def apply_details(program: Program, details: ProgramDetails) -> None:
    program.tagline = keep_or_replace(program.tagline, details.tagline)
    program.about = keep_or_replace(program.about, details.about)
    if details.audience:
        program.audience_intro = details.audience_intro
        program.audience = lines(details.audience)
    program.results = keep_or_replace(program.results, lines(details.results))
    program.hours = keep_or_replace(program.hours, details.hours)
    program.language = keep_or_replace(program.language, details.language)
    program.schedule = keep_or_replace(program.schedule, details.schedule)
    program.tax_refund = keep_or_replace(program.tax_refund, details.tax_refund)
    program.discounts = keep_or_replace(program.discounts, lines(details.discounts))
    program.admission_documents = keep_or_replace(program.admission_documents, lines(details.admission_documents))
    program.advantages = keep_or_replace(program.advantages, lines(details.advantages))
    notice = details.notice
    program.notice_date = notice.date if notice else ""
    program.notice_text = notice.text if notice else ""
    program.notice_url = notice.url if notice else ""
