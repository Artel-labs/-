import re
from dataclasses import dataclass

from django.utils import timezone
from django_q.models import OrmQ, Task
from django_q.tasks import async_task

from catalog.sync.runner import PROBLEMS_LABEL

SYNC_FUNCTION = "catalog.tasks.sync_catalog"
MANUAL_SYNC_NAME = "Обновление каталога с hse.ru (вручную)"
PROBLEMS = re.compile(rf"{PROBLEMS_LABEL}: (\d+)")
MAX_REASON_LENGTH = 300
TRACEBACK_MARK = " : Traceback"
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
    return any(entry.func() == SYNC_FUNCTION for entry in OrmQ.objects.all())


def last_run() -> Task | None:
    return Task.objects.filter(func=SYNC_FUNCTION).order_by("-stopped").first()


def problem_count(summary: str) -> int:
    found = PROBLEMS.search(summary)
    return int(found.group(1)) if found else 0


def summary_lines(summary: str) -> list[str]:
    first, *rest = summary.splitlines() or [""]
    return [part.strip() for part in first.split(";") if part.strip()] + [line for line in rest if line.strip()]


def failure_reason(result: object) -> str:
    first = (str(result or "").strip().splitlines() or [""])[0].split(TRACEBACK_MARK)[0].strip()
    return f"Причина: {first[:MAX_REASON_LENGTH]}" if first else ""


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
    task = last_run()
    return finished_state(task) if task else SyncState(False, True, NEVER, [])


def start_sync() -> bool:
    if is_running():
        return False
    async_task(SYNC_FUNCTION, task_name=MANUAL_SYNC_NAME)
    return True
