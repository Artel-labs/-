from typing import Any

from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest


class ViewOnly:
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


def take_over(*models: type[Model]) -> None:
    for model in models:
        if admin.site.is_registered(model):
            admin.site.unregister(model)
