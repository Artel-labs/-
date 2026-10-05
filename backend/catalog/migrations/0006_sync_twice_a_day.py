from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import migrations

SYNC_FUNCTION = "catalog.tasks.sync_catalog"
MINUTES = "I"
DAILY = "D"
HALF_DAY_MINUTES = 12 * 60
RUN_TIMES = (time(0, 0), time(12, 0))
OLD_TIME = time(4, 0)
MOSCOW = ZoneInfo("Europe/Moscow")


def next_moment(times: tuple[time, ...]) -> datetime:
    now = datetime.now(MOSCOW)
    days = (now.date(), now.date() + timedelta(days=1))
    moments = sorted(datetime.combine(day, moment, MOSCOW) for day in days for moment in times)
    return next(moment for moment in moments if moment > now)


def twice_a_day(apps, schema_editor):
    schedules = apps.get_model("django_q", "Schedule").objects.filter(func=SYNC_FUNCTION)
    schedules.update(schedule_type=MINUTES, minutes=HALF_DAY_MINUTES, next_run=next_moment(RUN_TIMES))


def once_a_day(apps, schema_editor):
    schedules = apps.get_model("django_q", "Schedule").objects.filter(func=SYNC_FUNCTION)
    schedules.update(schedule_type=DAILY, minutes=None, next_run=next_moment((OLD_TIME,)))


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_program_hidden_by_hand"),
        ("django_q", "0019_alter_task_options_alter_ormq_key_alter_ormq_lock_and_more"),
    ]

    operations = [migrations.RunPython(twice_a_day, once_a_day)]
