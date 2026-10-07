from django.utils.module_loading import import_string

from tasks.queue import task_title

RETENTION_TASKS = (
    "applications.tasks.purge_old_applications",
    "analytics.tasks.purge_old_events",
    "protection.tasks.purge_login_journal",
)


def purge_all() -> list[str]:
    return [f"{task_title(func)}: {import_string(func)()}" for func in RETENTION_TASKS]
