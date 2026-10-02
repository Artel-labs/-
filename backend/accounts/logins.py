from dataclasses import dataclass

from django.core.management.base import CommandError


@dataclass(frozen=True)
class LoginChoice:
    script: str
    nobody: str
    listed: str


def chosen_login(given: str | None, candidates: list[str], choice: LoginChoice) -> str:
    if given:
        return given
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise CommandError(choice.nobody)
    raise CommandError(f"{choice.listed}: {', '.join(candidates)}. Укажите логин: {choice.script} <логин>")
