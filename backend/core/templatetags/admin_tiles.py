from typing import Any

from django import template

from core.navigation import tiles

register = template.Library()


@register.simple_tag(takes_context=True)
def admin_tiles(context: template.Context) -> list[dict[str, Any]]:
    return tiles(context["request"])
