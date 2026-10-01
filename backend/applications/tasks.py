from applications.service import purge_expired


def purge_old_applications() -> str:
    return purge_expired()
