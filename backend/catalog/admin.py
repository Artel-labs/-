from typing import Any

from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import URLPattern, path, reverse
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import display

from catalog.formatting import format_price, unbreakable
from catalog.models import FaqItem, Module, Program, ProgramFile, ProgramTeacher, Review, Source, Sphere, Teacher
from catalog.publishing import FOLLOWS_HSE, follows_hse, remember_visibility, set_manual
from catalog.sync.fields import SYNCED_FIELDS
from catalog.sync.state import CATALOG, TEACHERS
from catalog.sync_admin import SyncLine
from core.steps import Step, Subject, run_step

PROGRAM_CARD = "admin/catalog/program/change_form.html"
SERVICE_FIELDS = ["hse_id", "source", "catalog_position", "created_at", "updated_at"]
STEPS = {
    "manual": Step(
        "Править вручную?",
        "Программа перестанет обновляться с hse.ru: ваши правки сохранятся, но новые данные с hse.ru сюда больше "
        "не придут. Вернуть обновление можно в любой момент.",
        "Править вручную",
        False,
        "Теперь программу можно править вручную. С hse.ru она больше не обновляется.",
    ),
    "follow": Step(
        "Вернуть обновление с hse.ru?",
        "При следующем обновлении данные программы заменятся данными с hse.ru, ручные правки текстов и списков "
        "пропадут.",
        "Вернуть обновление",
        True,
        "Программа снова обновляется с hse.ru.",
    ),
}
UPDATES_FROM_HSE = "Обновляется с hse.ru"
TABS = (("main", "Главное"), ("terms", "Условия и цена"), ("text", "Описание"), ("content", "Содержание"))


class FollowsHseInline(InlineModelAdmin):
    extra = 0
    ordering_field = "position"
    hide_ordering_field = True

    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> Any:
        return self.get_fields(request, obj) if follows_hse(obj) else super().get_readonly_fields(request, obj)

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return not follows_hse(obj) and bool(super().has_add_permission(request, obj))

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return not follows_hse(obj) and bool(super().has_delete_permission(request, obj))


class ModuleInline(FollowsHseInline, StackedInline):
    model = Module
    fields = ["title", "hours", "topics", "position"]


class ProgramTeacherInline(FollowsHseInline, TabularInline):
    model = ProgramTeacher
    autocomplete_fields = ["teacher"]
    fields = ["teacher", "about", "position"]


class ProgramFileInline(FollowsHseInline, TabularInline):
    model = ProgramFile
    fields = ["kind", "title", "file", "size_label", "source_url", "position"]


class FaqInline(FollowsHseInline, TabularInline):
    model = FaqItem
    fields = ["question", "answer", "position"]


class ReviewInline(FollowsHseInline, TabularInline):
    model = Review
    fields = ["text", "author", "position"]


class FollowsHseFilter(admin.SimpleListFilter):
    title = UPDATES_FROM_HSE
    parameter_name = "updates"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [("yes", "Да"), ("no", "Нет")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Program]) -> QuerySet[Program]:
        if self.value() == "yes":
            return queryset.filter(FOLLOWS_HSE)
        if self.value() == "no":
            return queryset.exclude(FOLLOWS_HSE)
        return queryset


@admin.register(Program)
class ProgramAdmin(SyncLine, ModelAdmin):
    sync_kind = CATALOG
    sync_button = "Обновить программы"
    list_display = [
        "title",
        "sphere",
        "type_short",
        "study_format",
        "start_date",
        "display_price",
        "updates_from_hse",
        "is_published",
    ]
    list_filter = ["sphere", "type_short", "study_format", FollowsHseFilter, "is_published", "source"]
    search_fields = ["title", "hse_id", "tagline"]
    list_select_related = ["sphere"]
    inlines = [ModuleInline, ProgramTeacherInline, ProgramFileInline, FaqInline, ReviewInline]
    change_form_template = PROGRAM_CARD
    fieldsets = [
        (
            "Главное",
            {
                "classes": ["dpo-tab-main"],
                "fields": ["title", "sphere", "position", "top_position", "is_published", "image"],
            },
        ),
        ("Служебное", {"classes": ["dpo-tab-main", "dpo-service"], "fields": ["hse_url", *SERVICE_FIELDS]}),
        (
            "Условия и цена",
            {
                "classes": ["dpo-tab-terms"],
                "fields": [
                    ("type_short", "type_title"),
                    "study_format",
                    ("start_date", "start_month_only"),
                    ("duration", "hours"),
                    ("language", "schedule"),
                    ("price", "base_price"),
                    "tax_refund",
                    "discounts",
                ],
            },
        ),
        (
            "Описание",
            {
                "classes": ["dpo-tab-text"],
                "fields": [
                    "tagline",
                    "about",
                    "audience_intro",
                    "audience",
                    "results",
                    "advantages",
                    "admission_documents",
                ],
            },
        ),
        (
            "Объявление на странице программы",
            {"classes": ["dpo-tab-text"], "fields": ["notice_date", "notice_text", "notice_url"]},
        ),
    ]

    class Media:
        js = ("catalog/program.js",)

    def get_readonly_fields(self, request: HttpRequest, obj: Program | None = None) -> Any:
        service = SERVICE_FIELDS if obj and obj.source == Source.HSE else SERVICE_FIELDS[1:]
        return [*service, *SYNCED_FIELDS] if follows_hse(obj) else service

    def get_urls(self) -> list[URLPattern]:
        view = self.admin_site.admin_view
        own = [
            *self.sync_patterns(),
            path("<path:object_id>/manual/", view(self.manual_view), name="catalog_program_manual"),
            path("<path:object_id>/follow-hse/", view(self.follow_view), name="catalog_program_follow"),
        ]
        inherited: list[URLPattern] = super().get_urls()
        return own + inherited

    def changeform_view(
        self, request: HttpRequest, object_id: Any = None, form_url: str = "", extra_context: Any = None
    ) -> Any:
        program = self.get_object(request, unquote(object_id)) if object_id else None
        context = {"tabs": TABS, "program": program, "follows_hse": follows_hse(program)}
        return super().changeform_view(request, object_id, form_url, {**(extra_context or {}), **context})

    def save_model(self, request: HttpRequest, obj: Program, form: Any, change: bool) -> None:
        remember_visibility(obj, "is_published" in form.changed_data)
        super().save_model(request, obj, form, change)

    def toggle(self, request: HttpRequest, object_id: str, name: str, manual: bool) -> HttpResponse:
        program = get_object_or_404(Program, pk=unquote(object_id))
        if program.source != Source.HSE or not self.has_change_permission(request, program):
            raise PermissionDenied
        card = reverse("admin:catalog_program_change", args=[program.pk])
        return run_step(
            self, request, STEPS[name], Subject("Программа", program.title), card, lambda: set_manual(program, manual)
        )

    def manual_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        return self.toggle(request, object_id, "manual", True)

    def follow_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        return self.toggle(request, object_id, "follow", False)

    @display(description=UPDATES_FROM_HSE, boolean=True)
    def updates_from_hse(self, program: Program) -> bool:
        return follows_hse(program)

    @display(description="Цена", ordering="price")
    def display_price(self, program: Program) -> str:
        return unbreakable(format_price(program.price)) if program.price else "—"


@admin.register(Sphere)
class SphereAdmin(ModelAdmin):
    list_display = ["title", "slug", "program_count"]
    ordering_field = "position"
    hide_ordering_field = True
    prepopulated_fields = {"slug": ["title"]}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Sphere]:
        queryset: QuerySet[Sphere] = super().get_queryset(request)
        return queryset.prefetch_related("programs")

    @display(description="Программ")
    def program_count(self, sphere: Sphere) -> int:
        return len(sphere.programs.all())


@admin.register(Teacher)
class TeacherAdmin(SyncLine, ModelAdmin):
    sync_kind = TEACHERS
    sync_button = "Обновить преподавателей"
    list_display = ["name", "page_url", "has_photo", "show_on_landing"]
    list_filter = ["show_on_landing"]
    search_fields = ["name"]

    class Media:
        js = ("catalog/program.js",)

    def get_urls(self) -> list[URLPattern]:
        inherited: list[URLPattern] = super().get_urls()
        return self.sync_patterns() + inherited

    @display(description="Фото", boolean=True)
    def has_photo(self, teacher: Teacher) -> bool:
        return bool(teacher.photo)
