from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

CONFIRM_TEMPLATE = "admin/dpo/confirm.html"


@dataclass(frozen=True)
class Step:
    title: str
    text: str
    button: str
    danger: bool
    done: str = ""


@dataclass(frozen=True)
class Subject:
    label: str
    name: str


def page_context(model_admin: "ModelAdmin[Any]", request: HttpRequest, title: str, back_url: str) -> dict[str, Any]:
    return {
        **model_admin.admin_site.each_context(request),
        "opts": model_admin.model._meta,
        "title": title,
        "back_url": back_url,
    }


def confirm_page(
    model_admin: "ModelAdmin[Any]", request: HttpRequest, step: Step, subject: Subject, back_url: str
) -> TemplateResponse:
    context = {**page_context(model_admin, request, step.title, back_url), "step": step, "subject": subject}
    return TemplateResponse(request, CONFIRM_TEMPLATE, context)


def run_step(
    model_admin: "ModelAdmin[Any]",
    request: HttpRequest,
    step: Step,
    subject: Subject,
    back_url: str,
    perform: Callable[[], HttpResponse | None],
) -> HttpResponse:
    if request.method != "POST":
        return confirm_page(model_admin, request, step, subject, back_url)
    result = perform()
    if isinstance(result, HttpResponse):
        return result
    messages.success(request, step.done)
    return HttpResponseRedirect(back_url)
