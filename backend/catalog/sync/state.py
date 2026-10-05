import re
from dataclasses import dataclass

from django.utils import timezone
from django_q.models import Task

from catalog.sync.runner import PROBLEMS_LABEL
from tasks.queue import MANUAL_SUFFIX, first_line, is_queued, last_run, start_once, task_title

PROBLEMS = re.compile(rf"{PROBLEMS_LABEL}: (\d+)")
FAILED = "не удалось"
SUCCEEDED = "успешно"
WITH_PROBLEMS = "с проблемами ({count})"


@dataclass(frozen=True)
class SyncKind:
    function: str
    running: str
    never: str
    last: str

    @property
    def manual_name(self) -> str:
        return task_title(self.function) + MANUAL_SUFFIX


CATALOG = SyncKind(
    "catalog.tasks.sync_catalog",
    "Идёт обновление каталога с hse.ru…",
    "Каталог ещё не обновлялся с hse.ru.",
    "Последнее обновление с hse.ru: {when} — {outcome}.",
)
TEACHERS = SyncKind(
    "catalog.tasks.sync_teachers",
    "Идёт обновление преподавателей с hse.ru…",
    "Преподаватели ещё не обновлялись отдельно. Они обновляются и вместе с каталогом.",
    "Последнее обновление преподавателей: {when} — {outcome}.",
)
KINDS = (CATALOG, TEACHERS)
SYNC_FUNCTION = CATALOG.function


@dataclass(frozen=True)
class SyncState:
    running: bool
    ok: bool
    headline: str
    lines: list[str]


def running_kind() -> SyncKind | None:
    return next((kind for kind in KINDS if is_queued(kind.function)), None)


def is_running() -> bool:
    return running_kind() is not None


def problem_count(summary: str) -> int:
    found = PROBLEMS.search(summary)
    return int(found.group(1)) if found else 0


def summary_lines(summary: str) -> list[str]:
    first, *rest = summary.splitlines() or [""]
    return [part.strip() for part in first.split(";") if part.strip()] + [line for line in rest if line.strip()]


def failure_reason(result: object) -> str:
    line = first_line(result)
    return f"Причина: {line}" if line else ""


def when(task: Task) -> str:
    return timezone.localtime(task.stopped).strftime("%d.%m.%Y, %H:%M")


def finished_state(kind: SyncKind, task: Task) -> SyncState:
    if not task.success:
        reason = failure_reason(task.result)
        return SyncState(False, False, kind.last.format(when=when(task), outcome=FAILED), [reason] if reason else [])
    summary = str(task.result or "")
    count = problem_count(summary)
    outcome = WITH_PROBLEMS.format(count=count) if count else SUCCEEDED
    return SyncState(False, count == 0, kind.last.format(when=when(task), outcome=outcome), summary_lines(summary))


def sync_state(kind: SyncKind = CATALOG) -> SyncState:
    busy = running_kind()
    if busy:
        return SyncState(True, True, busy.running, [])
    task = last_run(kind.function)
    return finished_state(kind, task) if task else SyncState(False, True, kind.never, [])


def start_sync(kind: SyncKind = CATALOG) -> bool:
    return start_once(kind.function, kind.manual_name)
