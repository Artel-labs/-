from protection.journal_retention import purge_old_journal


def purge_login_journal() -> str:
    return purge_old_journal()
