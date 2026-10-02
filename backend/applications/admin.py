import smtplib
from typing import Any

from django import forms
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget

from applications.mail import send_test_mail, test_mail_problem
from applications.models import Application, MailRecipient, Source, Status, Topic, all_topics
from applications.recipients import all_recipients
from applications.service import resend

NO_RECIPIENTS = (
    "Письма по заявкам не отправляются: нет активных получателей. Добавьте их в «Заявки» → «Получатели писем»."
)


@admin.register(Application)
class ApplicationAdmin(ModelAdmin):
    list_display = ["received_at", "full_name", "topic", "program_title", "phone", "email", "status", "mail_status"]
    list_display_links = ["received_at", "full_name"]
    list_editable = ["status"]
    list_filter = ["status", "topic", "applicant_type", "mail_status", "received_at"]
    search_fields = ["last_name", "first_name", "email", "phone", "company", "program_title"]
    date_hierarchy = "received_at"
    actions = ["mark_in_progress", "mark_done", "mark_rejected", "resend_mail"]
    actions_list = ["check_mail"]
    actions_detail = ["resend_one"]
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
        "mail_attempts",
    ]
    fieldsets = [
        ("Заявка", {"fields": ["status", "received_at", "topic", "program", "program_title", "comment"]}),
        ("Заявитель", {"fields": ["last_name", "first_name", "phone", "email", "position", "company"]}),
        ("Организация", {"fields": ["applicant_type", "employees_count", "timeframe"]}),
        ("Дополнительно", {"fields": ["sources_text", "source_other", "no_announcements"]}),
        ("Письмо учебному офису", {"fields": ["mail_status", "mail_error", "mail_attempts"]}),
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

    @admin.action(description="Отправить письмо ещё раз")
    def resend_mail(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.report_resend(request, list(queryset))

    @action(
        description="Отправить письмо ещё раз", url_path="resend-mail", icon="forward_to_inbox", permissions=["change"]
    )
    def resend_one(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        self.report_resend(request, list(Application.objects.filter(pk=object_id)))
        return HttpResponseRedirect(reverse("admin:applications_application_change", args=[object_id]))

    def report_resend(self, request: HttpRequest, applications: list[Application]) -> None:
        queued = resend(applications)
        skipped = len(applications) - queued
        text = f"Письма поставлены в очередь: {queued}."
        if skipped:
            text += f" Уже были отправлены, пропущено: {skipped}."
        self.message_user(request, text)

    @action(description="Проверить почту", url_path="check-mail", icon="mail", permissions=["change"])
    def check_mail(self, request: HttpRequest) -> HttpResponseRedirect:
        back = HttpResponseRedirect(reverse("admin:applications_application_changelist"))
        problem = test_mail_problem()
        if problem:
            self.message_user(request, problem, messages.WARNING)
            return back
        try:
            send_test_mail()
        except (smtplib.SMTPException, OSError) as error:
            self.message_user(request, f"Письмо не ушло: {error}", messages.ERROR)
            return back
        self.message_user(request, f"Пробное письмо отправлено: {', '.join(all_recipients())}.")
        return back

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, Any] | None = None) -> HttpResponse:
        if request.method == "GET" and not all_recipients():
            self.message_user(request, NO_RECIPIENTS, messages.WARNING)
        response: HttpResponse = super().changelist_view(request, extra_context)
        return response


class MailRecipientForm(forms.ModelForm):
    topics = forms.MultipleChoiceField(
        label="Темы заявок",
        choices=Topic.choices,
        initial=all_topics,
        widget=UnfoldAdminCheckboxSelectMultipleWidget,
        help_text="Письма по заявкам на отмеченные темы придут на этот адрес.",
    )

    class Meta:
        model = MailRecipient
        fields = ["email", "note", "topics", "is_active"]


@admin.register(MailRecipient)
class MailRecipientAdmin(ModelAdmin):
    form = MailRecipientForm
    list_display = ["email", "note", "topics_text", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["email", "note"]

    @display(description="Темы заявок")
    def topics_text(self, recipient: MailRecipient) -> str:
        return ", ".join(Topic(topic).label for topic in recipient.topics if topic in Topic.values)
