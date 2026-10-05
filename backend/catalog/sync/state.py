import re
from dataclasses import dataclass

from django.utils import timezone
from django_q.models import Task

from catalog.sync.runner import PROBLEMS_LABEL
from tasks.queue import MANUAL_SUFFIX, first_line, is_queued, last_run, start_once, task_title

SYNC_FUNCTION = "catalog.tasks.sync_catalog"
MANUAL_SYNC_NAME = task_title(SYNC_FUNCTION) + MANUAL_SUFFIX
PROBLEMS = re.compile(rf"{PROBLEMS_LABEL}: (\d+)")
RUNNING = "Идёт обновление каталога с hse.ru…"
NEVER = "Каталог ещё не обновлялся с hse.ru."
LAST = "Последнее обновление с hse.ru: {when} — {outcome}."
FAILED = "не удалось"
SUCCEEDED = "успешно"
WITH_PROBLEMS = "с проблемами ({count})"


@dataclass(frozen=True)
class SyncState:
    running: bool
    ok: bool
    headline: str
    lines: list[str]


def is_running() -> bool:
    return is_queued(SYNC_FUNCTION)


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


def finished_state(task: Task) -> SyncState:
    if not task.success:
        reason = failure_reason(task.result)
        return SyncState(False, False, LAST.format(when=when(task), outcome=FAILED), [reason] if reason else [])
    summary = str(task.result or "")
    count = problem_count(summary)
    outcome = WITH_PROBLEMS.format(count=count) if count else SUCCEEDED
    return SyncState(False, count == 0, LAST.format(when=when(task), outcome=outcome), summary_lines(summary))


def sync_state() -> SyncState:
    if is_running():
        return SyncState(True, True, RUNNING, [])
    task = last_run(SYNC_FUNCTION)
    return finished_state(task) if task else SyncState(False, True, NEVER, [])


def start_sync() -> bool:
    return start_once(SYNC_FUNCTION, MANUAL_SYNC_NAME)
