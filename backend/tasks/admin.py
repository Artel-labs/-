from datetime import timedelta
from typing import Any

from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import URLPattern, path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django_q.models import Failure, OrmQ, Schedule, Success
from unfold.admin import ModelAdmin
from unfold.decorators import display

from core.admin_tools import ViewOnly, take_over
from tasks.models import PlannedTask, TaskRecord
from tasks.queue import first_line, frequency, last_run, run_now, task_title

DATE_FORMAT = "%d.%m.%Y, %H:%M"
NEVER = "ещё не запускалась"
STARTED = "Запущено: {title}. Итог появится в «Журнале задач»."
BUSY = "{title} уже выполняется — дождитесь итога."
OK = "ok"
FAILED = "failed"
OUTCOMES = {True: "Успешно", False: "Ошибка"}

take_over(Schedule, Success, Failure, OrmQ)


def moment(value: Any) -> str:
    return timezone.localtime(value).strftime(DATE_FORMAT) if value else "—"


def seconds(span: timedelta) -> str:
    total = int(span.total_seconds())
    return f"{total // 60} мин {total % 60} с" if total >= 60 else f"{total} с"


def outcome_badge(success: bool) -> str:
    return format_html('<span class="dpo-badge dpo-badge-{}">{}</span>', OK if success else FAILED, OUTCOMES[success])


@admin.register(PlannedTask)
class PlannedTaskAdmin(ViewOnly, ModelAdmin):
    list_display = ["title", "how_often", "next_time", "last_time", "run_button"]
    list_display_links = None
    ordering = ["next_run"]

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        return {}

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def get_urls(self) -> list[URLPattern]:
        own = [path("<path:object_id>/run/", self.admin_site.admin_view(self.run_view), name="tasks_plannedtask_run")]
        inherited: list[URLPattern] = super().get_urls()
        return own + inherited

    @display(description="Задача")
    def title(self, schedule: PlannedTask) -> str:
        return task_title(schedule.func, schedule.name or "")

    @display(description="Как часто")
    def how_often(self, schedule: PlannedTask) -> str:
        return frequency(schedule)

    @display(description="Следующий запуск", ordering="next_run")
    def next_time(self, schedule: PlannedTask) -> str:
        return moment(schedule.next_run)

    @display(description="Последний запуск")
    def last_time(self, schedule: PlannedTask) -> str:
        task = last_run(schedule.func)
        if not task:
            return NEVER
        return format_html("{} {}", moment(task.stopped), outcome_badge(bool(task.success)))

    @display(description="")
    def run_button(self, schedule: PlannedTask) -> str:
        url = reverse("admin:tasks_plannedtask_run", args=[schedule.pk])
        return format_html(
            '<button type="submit" class="dpo-chip" formaction="{}" formmethod="post">Запустить сейчас</button>', url
        )

    def run_view(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        if request.method != "POST" or not self.has_view_permission(request):
            raise PermissionDenied
        schedule = get_object_or_404(PlannedTask, pk=unquote(object_id))
        title = task_title(schedule.func, schedule.name or "")
        if run_now(schedule):
            messages.success(request, STARTED.format(title=title))
        else:
            messages.warning(request, BUSY.format(title=title))
        return HttpResponseRedirect(reverse("admin:tasks_plannedtask_changelist"))


class OutcomeFilter(admin.SimpleListFilter):
    title = "Итог"
    parameter_name = "outcome"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [(OK, OUTCOMES[True]), (FAILED, OUTCOMES[False])]

    def queryset(self, request: HttpRequest, queryset: QuerySet[TaskRecord]) -> QuerySet[TaskRecord]:
        if self.value() in (OK, FAILED):
            return queryset.filter(success=self.value() == OK)
        return queryset


@admin.register(TaskRecord)
class TaskRecordAdmin(ViewOnly, ModelAdmin):
    list_display = ["title", "outcome", "started_at", "duration", "summary"]
    list_display_links = ["title"]
    list_filter = [OutcomeFilter]
    search_fields = ["name", "func"]
    ordering = ["-stopped"]
    fields = ["title", "outcome", "started_at", "stopped_at", "duration", "full_result"]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @display(description="Задача")
    def title(self, task: TaskRecord) -> str:
        return task_title(task.func, task.name)

    @display(description="Итог")
    def outcome(self, task: TaskRecord) -> str:
        return outcome_badge(bool(task.success))

    @display(description="Начало", ordering="started")
    def started_at(self, task: TaskRecord) -> str:
        return moment(task.started)

    @display(description="Конец")
    def stopped_at(self, task: TaskRecord) -> str:
        return moment(task.stopped)

    @display(description="Длительность")
    def duration(self, task: TaskRecord) -> str:
        return seconds(task.stopped - task.started) if task.started and task.stopped else "—"

    @display(description="Итог кратко")
    def summary(self, task: TaskRecord) -> str:
        return first_line(task.result) or "—"

    @display(description="Полный итог")
    def full_result(self, task: TaskRecord) -> str:
        return format_html('<pre class="dpo-pre">{}</pre>', str(task.result or "—"))
