from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import display

from catalog.models import FaqItem, Module, Program, ProgramFile, ProgramTeacher, Review, Sphere, Teacher


class OrderedTabularInline(TabularInline):
    extra = 0
    tab = True
    ordering_field = "position"
    hide_ordering_field = True


class ModuleInline(StackedInline):
    model = Module
    extra = 0
    tab = True
    ordering_field = "position"
    hide_ordering_field = True
    fields = ["title", "hours", "topics", "position"]


class ProgramTeacherInline(OrderedTabularInline):
    model = ProgramTeacher
    autocomplete_fields = ["teacher"]
    fields = ["teacher", "about", "position"]


class ProgramFileInline(OrderedTabularInline):
    model = ProgramFile
    fields = ["kind", "title", "file", "size_label", "source_url", "position"]


class FaqInline(OrderedTabularInline):
    model = FaqItem
    fields = ["question", "answer", "position"]


class ReviewInline(OrderedTabularInline):
    model = Review
    fields = ["text", "author", "position"]


@admin.register(Program)
class ProgramAdmin(ModelAdmin):
    list_display = [
        "title",
        "sphere",
        "type_short",
        "study_format",
        "start_date",
        "display_price",
        "locked",
        "is_published",
    ]
    list_filter = ["sphere", "type_short", "study_format", "locked", "is_published", "source"]
    search_fields = ["title", "hse_id", "tagline"]
    list_select_related = ["sphere"]
    readonly_fields = ["source", "created_at", "updated_at"]
    inlines = [ModuleInline, ProgramTeacherInline, ProgramFileInline, FaqInline, ReviewInline]
    fieldsets = [
        (
            "Основное",
            {
                "classes": ["tab"],
                "fields": [
                    "title",
                    "hse_id",
                    "sphere",
                    "position",
                    "is_published",
                    "locked",
                    "source",
                    "hse_url",
                    "image",
                ],
            },
        ),
        (
            "Условия",
            {
                "classes": ["tab"],
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
                "classes": ["tab"],
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
        ("Объявление", {"classes": ["tab"], "fields": ["notice_date", "notice_text", "notice_url"]}),
        ("Служебное", {"classes": ["tab"], "fields": ["created_at", "updated_at"]}),
    ]

    @display(description="Цена", ordering="price")
    def display_price(self, program: Program) -> str:
        return f"{program.price:,} ₽".replace(",", " ") if program.price else "—"


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
class TeacherAdmin(ModelAdmin):
    list_display = ["name", "page_url", "has_photo"]
    search_fields = ["name"]

    @display(description="Фото", boolean=True)
    def has_photo(self, teacher: Teacher) -> bool:
        return bool(teacher.photo)
