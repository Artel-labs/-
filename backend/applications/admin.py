import smtplib

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import action, display

from applications.mail import mail_configured, send_test_mail
from applications.models import Application, Source, Status

MAIL_NOT_CONFIGURED = "Почта не настроена: укажите SMTP_HOST и APPLICATION_MAIL_TO в файле .env на сервере."


@admin.register(Application)
class ApplicationAdmin(ModelAdmin):
    list_display = ["received_at", "full_name", "topic", "program_title", "phone", "email", "status", "mail_status"]
    list_display_links = ["received_at", "full_name"]
    list_editable = ["status"]
    list_filter = ["status", "topic", "applicant_type", "mail_status", "received_at"]
    search_fields = ["last_name", "first_name", "email", "phone", "company", "program_title"]
    date_hierarchy = "received_at"
    actions = ["mark_in_progress", "mark_done", "mark_rejected"]
    actions_list = ["check_mail"]
    readonly_fields = [
        "received_at",
        "topic",
        "applicant_type",
        "employees_count",
        "timeframe",
        "first_name",
        "last_name",
        "phone",
        "email",
        "position",
        "company",
        "sources_text",
        "source_other",
        "comment",
        "no_announcements",
        "program",
        "program_title",
        "mail_status",
        "mail_error",
    ]
    fieldsets = [
        ("Заявка", {"fields": ["status", "received_at", "topic", "program", "program_title", "comment"]}),
        ("Заявитель", {"fields": ["last_name", "first_name", "phone", "email", "position", "company"]}),
        ("Организация", {"fields": ["applicant_type", "employees_count", "timeframe"]}),
        ("Дополнительно", {"fields": ["sources_text", "source_other", "no_announcements"]}),
        ("Письмо учебному офису", {"fields": ["mail_status", "mail_error"]}),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @display(description="Заявитель", ordering="last_name")
    def full_name(self, application: Application) -> str:
        return application.full_name

    @display(description="Откуда узнали")
    def sources_text(self, application: Application) -> str:
        return ", ".join(Source(source).label for source in application.sources)

    def change_status(self, request: HttpRequest, queryset: QuerySet[Application], status: Status) -> None:
        updated = queryset.update(status=status)
        self.message_user(request, f"Статус «{status.label}» у заявок: {updated}")

    @admin.action(description="Отметить «В работе»")
    def mark_in_progress(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.change_status(request, queryset, Status.IN_PROGRESS)

    @admin.action(description="Отметить «Обработана»")
    def mark_done(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.change_status(request, queryset, Status.DONE)

    @admin.action(description="Отметить «Отклонена»")
    def mark_rejected(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.change_status(request, queryset, Status.REJECTED)

    @action(description="Проверить почту", url_path="check-mail", icon="mail", permissions=["change"])
    def check_mail(self, request: HttpRequest) -> HttpResponseRedirect:
        back = HttpResponseRedirect(reverse("admin:applications_application_changelist"))
        if not mail_configured():
            self.message_user(request, MAIL_NOT_CONFIGURED, messages.WARNING)
            return back
        try:
            send_test_mail()
        except (smtplib.SMTPException, OSError) as error:
            self.message_user(request, f"Письмо не ушло: {error}", messages.ERROR)
            return back
        self.message_user(request, "Пробное письмо отправлено. Проверьте ящик учебного офиса.")
        return back
