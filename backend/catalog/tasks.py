from catalog.hse.client import HseClient
from catalog.sync.runner import run_sync
from catalog.sync.teachers import run_teacher_sync


def sync_catalog() -> str:
    with HseClient() as client:
        return run_sync(client).summary()


def sync_teachers() -> str:
    with HseClient() as client:
        return run_teacher_sync(client).summary()
