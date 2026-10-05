import re

from django.utils import timezone
from django_q.models import OrmQ, Schedule, Task
from django_q.tasks import async_task

MAX_SUMMARY_LENGTH = 300
TRACEBACK_MARK = " : Traceback"
CYRILLIC = re.compile("[а-яё]", re.IGNORECASE)
MANUAL_SUFFIX = " (вручную)"
TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%d.%m.%Y, %H:%M"
TASK_TITLES = {
    "catalog.tasks.sync_catalog": "Обновление каталога с hse.ru",
    "applications.tasks.purge_old_applications": "Удаление старых заявок",
    "analytics.tasks.purge_old_events": "Удаление старой аналитики",
    "applications.mail.send_application_mail": "Письмо по заявке",
}
WEEKDAYS = ("понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье")


def task_title(func: str, name: str = "") -> str:
    if name and CYRILLIC.search(name):
        return name
    return TASK_TITLES.get(func, func)


def first_line(result: object) -> str:
    line = (str(result or "").strip().splitlines() or [""])[0]
    return line.split(TRACEBACK_MARK)[0].strip()[:MAX_SUMMARY_LENGTH]


def is_queued(func: str) -> bool:
    return any(entry.func() == func for entry in OrmQ.objects.all())


def start_once(func: str, name: str) -> bool:
    if is_queued(func):
        return False
    async_task(func, task_name=name)
    return True


def last_run(func: str) -> Task | None:
    return Task.objects.filter(func=func).order_by("-stopped").first()


def frequency(schedule: Schedule) -> str:
    moment = timezone.localtime(schedule.next_run) if schedule.next_run else None
    at = moment.strftime(TIME_FORMAT) if moment else ""
    patterns = {
        Schedule.DAILY: f"каждый день в {at}",
        Schedule.WEEKLY: f"каждую {WEEKDAYS[moment.weekday()]} в {at}" if moment else "каждую неделю",
        Schedule.HOURLY: "каждый час",
        Schedule.MINUTES: f"каждые {schedule.minutes} мин",
        Schedule.MONTHLY: "каждый месяц",
        Schedule.ONCE: f"один раз — {moment.strftime(DATE_FORMAT)}" if moment else "один раз",
    }
    return patterns.get(schedule.schedule_type, str(schedule.get_schedule_type_display()))


def run_now(schedule: Schedule) -> bool:
    return start_once(schedule.func, task_title(schedule.func, schedule.name or "") + MANUAL_SUFFIX)
