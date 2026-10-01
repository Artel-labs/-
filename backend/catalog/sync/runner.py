import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial

import httpx
from django.conf import settings
from django.db import transaction

from catalog.hse.client import HseClient, HseError
from catalog.hse.details import ProgramDetails, parse_details
from catalog.hse.listing import ListedProgram, fetch_listing
from catalog.models import Program, ProgramFile, Source, Sphere, Teacher
from catalog.spheres import ensure_spheres
from catalog.sync.fields import apply_details, apply_listing
from catalog.sync.media import ensure_cover, ensure_teacher_photo, refresh_document
from catalog.sync.related import replace_related

NETWORK_ERRORS = (HseError, httpx.HTTPError, OSError)


@dataclass
class SyncReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    locked: list[str] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)
    downloads: int = 0
    problems: list[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [
            f"Новых программ: {len(self.created)}",
            f"обновлено: {len(self.updated)}",
            f"защищено от обновления: {len(self.locked)}",
            f"скрыто (нет на hse.ru): {len(self.hidden)}",
            f"скачано файлов: {self.downloads}",
            f"проблем: {len(self.problems)}",
        ]
        details = [f"Скрыты: {', '.join(self.hidden)}"] if self.hidden else []
        details += [f"— {problem}" for problem in self.problems]
        return "\n".join(["; ".join(parts), *details])


@transaction.atomic
def store_program(
    program: Program | None, item: ListedProgram, details: ProgramDetails, spheres: dict[str, Sphere]
) -> tuple[Program, list[Teacher], list[ProgramFile]]:
    saved = apply_listing(program, item, spheres)
    apply_details(saved, details)
    saved.save()
    teachers, documents = replace_related(saved, details)
    return saved, teachers, documents


def attempt(report: SyncReport, label: str, download: Callable[[], bool]) -> None:
    try:
        report.downloads += int(download())
    except NETWORK_ERRORS as error:
        report.problems.append(f"{label}: {error}")


def download_media(client: HseClient, report: SyncReport, program: Program, details: ProgramDetails) -> None:
    attempt(report, f"обложка «{program.title}»", partial(ensure_cover, client, program, details.image_url))
    photos = {item.name: item.photo_url for item in details.teachers}
    for link in program.program_teachers.select_related("teacher"):
        teacher = link.teacher
        url = photos.get(teacher.name, "")
        attempt(report, f"фото {teacher.name}", partial(ensure_teacher_photo, client, teacher, url))
    for document in program.files.all():
        attempt(report, f"{document.title} «{program.title}»", partial(refresh_document, client, document))


def sync_program(client: HseClient, report: SyncReport, item: ListedProgram, spheres: dict[str, Sphere]) -> None:
    program = Program.objects.filter(hse_id=item.hse_id).first()
    if program and program.locked:
        report.locked.append(program.title)
        return
    try:
        details = parse_details(client.html(item.url))
    except NETWORK_ERRORS as error:
        report.problems.append(f"страница «{item.title}»: {error}")
        return
    saved, _, _ = store_program(program, item, details, spheres)
    (report.updated if program else report.created).append(saved.title)
    download_media(client, report, saved, details)


def hide_missing(report: SyncReport, listed: list[ListedProgram]) -> None:
    missing = Program.objects.filter(source=Source.HSE, locked=False, is_published=True).exclude(
        hse_id__in=[item.hse_id for item in listed]
    )
    report.hidden = list(missing.values_list("title", flat=True))
    missing.update(is_published=False)


def run_sync(client: HseClient, pause: Callable[[float], None] = time.sleep) -> SyncReport:
    report = SyncReport()
    listed = fetch_listing(client)
    spheres = ensure_spheres()
    for item in listed:
        sync_program(client, report, item, spheres)
        pause(settings.HSE_REQUEST_DELAY_SECONDS)
    hide_missing(report, listed)
    return report
