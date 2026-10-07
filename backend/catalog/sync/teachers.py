import time
from collections.abc import Callable
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction

from catalog.hse.client import HseClient
from catalog.hse.details import ProgramDetails, parse_details
from catalog.models import Program
from catalog.publishing import FOLLOWS_HSE
from catalog.sync.related import replace_teachers
from catalog.sync.runner import NETWORK_ERRORS, PROBLEMS_LABEL, download_teacher_photos
from catalog.typesetting import typeset_record


@dataclass
class TeacherReport:
    programs: int = 0
    teachers: int = 0
    downloads: int = 0
    problems: list[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [
            f"Программ: {self.programs}",
            f"преподавателей: {self.teachers}",
            f"скачано фото: {self.downloads}",
            f"{PROBLEMS_LABEL}: {len(self.problems)}",
        ]
        return "\n".join(["; ".join(parts), *[f"— {problem}" for problem in self.problems]])


def followed_programs() -> list[Program]:
    return list(Program.objects.filter(FOLLOWS_HSE).exclude(hse_url="").order_by("catalog_position"))


@transaction.atomic
def store_teachers(program: Program, details: ProgramDetails) -> int:
    teachers = replace_teachers(program, details)
    for link in program.program_teachers.all():
        typeset_record(link)
    return len(teachers)


def refresh_program(client: HseClient, report: TeacherReport, program: Program) -> None:
    try:
        details = parse_details(client.html(program.hse_url))
    except NETWORK_ERRORS as error:
        report.problems.append(f"страница «{program.title}»: {error}")
        return
    report.programs += 1
    report.teachers += store_teachers(program, details)
    download_teacher_photos(client, report, program, details)


def run_teacher_sync(client: HseClient, pause: Callable[[float], None] = time.sleep) -> TeacherReport:
    report = TeacherReport()
    for program in followed_programs():
        refresh_program(client, report, program)
        pause(settings.HSE_REQUEST_DELAY_SECONDS)
    return report
