from analytics.service import purge_expired


def purge_old_events() -> str:
    return purge_expired()
