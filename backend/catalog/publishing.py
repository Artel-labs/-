from catalog.models import Program, Source


def follows_hse(program: Program | None) -> bool:
    return bool(program and program.source == Source.HSE and not program.locked)


def remember_visibility(program: Program, visibility_changed: bool) -> None:
    if visibility_changed:
        program.hidden_by_hand = not program.is_published


def set_manual(program: Program, manual: bool) -> None:
    program.locked = manual
    program.save(update_fields=["locked", "updated_at"])
