from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import migrations

SCHEDULE_NAME = "Удаление событий посещаемости старше срока хранения"
PURGE_FUNCTION = "analytics.tasks.purge_old_events"
DAILY = "D"
FOREVER = -1
PURGE_TIME = time(3, 40)
MOSCOW = ZoneInfo("Europe/Moscow")


def next_run() -> datetime:
    now = datetime.now(MOSCOW)
    run = datetime.combine(now.date(), PURGE_TIME, MOSCOW)
    return run if run > now else run + timedelta(days=1)


def create_schedule(apps, schema_editor):
    schedule = apps.get_model("django_q", "Schedule")
    schedule.objects.get_or_create(
        name=SCHEDULE_NAME,
        defaults={"func": PURGE_FUNCTION, "schedule_type": DAILY, "repeats": FOREVER, "next_run": next_run()},
    )


def remove_schedule(apps, schema_editor):
    apps.get_model("django_q", "Schedule").objects.filter(name=SCHEDULE_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
        ("django_q", "0019_alter_task_options_alter_ormq_key_alter_ormq_lock_and_more"),
    ]

    operations = [migrations.RunPython(create_schedule, remove_schedule)]
