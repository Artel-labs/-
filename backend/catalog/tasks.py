from catalog.hse.client import HseClient
from catalog.sync.runner import run_sync


def sync_catalog() -> str:
    with HseClient() as client:
        return run_sync(client).summary()
