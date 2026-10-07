import smtplib
from typing import Any

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import URLPattern, path, reverse
from django.utils.html import format_html, format_html_join
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget

from applications.card import card_of
from applications.mail import send_test_mail, test_mail_problem
from applications.mail_state import NOT_CONFIGURED, mail_state
from applications.models import Application, MailRecipient, Status, Topic, all_topics
from applications.recipients import all_recipients
from applications.service import resend, set_status, withdraw_ads_consent

STATUS_SAVED = "Статус: {label}."
WRONG_STATUS = "Такого статуса нет."
CARD_TEMPLATE = "admin/applications/application/card.html"


def wants_json(request: HttpRequest) -> bool:
    return "application/json" in request.headers.get("Accept", "")


@admin.register(Application)
class ApplicationAdmin(ModelAdmin):
    list_display = [
        "received_at",
        "full_name",
        "topic",
        "program_title",
        "phone",
        "email",
        "status_control",
        "mail_status",
    ]
    list_display_links = ["received_at", "full_name"]
    list_filter = ["status", "topic", "applicant_type", "mail_status", "received_at"]
    search_fields = ["last_name", "first_name", "email", "phone", "company", "program_title"]
    actions = ["mark_in_progress", "mark_done", "mark_rejected", "resend_mail", "withdraw_ads_consent"]
    list_before_template = "admin/applications/application/mail_state.html"
    change_form_template = CARD_TEMPLATE
    fields = ["status"]

    class Media:
        js = ("applications/status.js",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def get_list_display(self, request: HttpRequest) -> Any:
        if self.has_change_permission(request):
            return self.list_display
        return [name if name != "status_control" else "status" for name in self.list_display]

    def get_urls(self) -> list[URLPattern]:
        view = self.admin_site.admin_view
        own = [
            path("check-mail/", view(self.check_mail_view), name="applications_application_check_mail"),
            path("<path:object_id>/status/", view(self.status_view), name="applications_application_status"),
            path("<path:object_id>/resend/", view(self.resend_view), name="applications_application_resend"),
        ]
        inherited: list[URLPattern] = super().get_urls()
        return own + inherited

    def change_view(
        self, request: HttpRequest, object_id: str, form_url: str = "", extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        application = self.get_object(request, unquote(object_id))
        card = {"card": card_of(application), "show_save": False} if application else {}
        response: HttpResponse = super().change_view(request, object_id, form_url, {**(extra_context or {}), **card})
        return response

    @display(description="Заявитель", ordering="last_name")
    def full_name(self, application: Application) -> str:
        return application.full_name

    @display(description="Статус", ordering="status")
    def status_control(self, application: Application) -> str:
        options = format_html_join(
            "",
            '<option value="{}"{}>{}</option>',
            ((value, " selected" if value == application.status else "", label) for value, label in Status.choices),
        )
        return format_html(
            '<select class="dpo-status-select dpo-status-{}" data-status-url="{}" data-current="{}" '
            'aria-label="Статус заявки">{}</select>',
            application.status,
            reverse("admin:applications_application_status", args=[application.pk]),
            application.status,
            options,
        )

    def change_status(self, request: HttpRequest, queryset: QuerySet[Application], status: Status) -> None:
        updated = set_status(queryset, status)
        self.message_user(request, f"Статус «{status.label}» у заявок: {updated}")

    @admin.action(description="В работу")
    def mark_in_progress(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.change_status(request, queryset, Status.IN_PROGRESS)

    @admin.action(description="Обработана")
    def mark_done(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.change_status(request, queryset, Status.DONE)

    @admin.action(description="Отклонена")
    def mark_rejected(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.change_status(request, queryset, Status.REJECTED)

    @admin.action(description="Отправить письмо ещё раз")
    def resend_mail(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        self.report_resend(request, list(queryset))

    @admin.action(description="Отметить отзыв согласия на рассылку")
    def withdraw_ads_consent(self, request: HttpRequest, queryset: QuerySet[Application]) -> None:
        withdrawn = withdraw_ads_consent(queryset)
        self.message_user(request, f"Отзыв согласия на рассылку отмечен у заявок: {withdrawn}")

    def editable(self, request: HttpRequest, object_id: str) -> Application:
        if request.method != "POST":
            raise PermissionDenied
        application = get_object_or_404(Application, pk=unquote(object_id))
        if not self.has_change_permission(request, application):
            raise PermissionDenied
        return application

    def card_redirect(self, application: Application) -> HttpResponseRedirect:
        return HttpResponseRedirect(reverse("admin:applications_application_change", args=[application.pk]))

    def status_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        application = self.editable(request, object_id)
        value = request.POST.get("status", "")
        if value not in Status.values:
            return JsonResponse({"error": WRONG_STATUS}, status=400)
        status = Status(value)
        set_status(Application.objects.filter(pk=application.pk), status)
        if wants_json(request):
            return JsonResponse({"status": status.value, "label": str(status.label)})
        self.message_user(request, STATUS_SAVED.format(label=status.label))
        return self.card_redirect(application)

    def resend_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        application = self.editable(request, object_id)
        self.report_resend(request, [application])
        return self.card_redirect(application)

    def report_resend(self, request: HttpRequest, applications: list[Application]) -> None:
        result = resend(applications)
        if result.queued:
            self.message_user(request, f"Письма поставлены в очередь: {result.queued}.")
        if result.already_sent:
            self.message_user(request, f"Уже были отправлены, пропущено: {result.already_sent}.", messages.INFO)
        for reason, count in result.blocked.items():
            self.message_user(request, f"Не отправлено ({count}): {reason}", messages.WARNING)

    def check_mail_view(self, request: HttpRequest) -> HttpResponseRedirect:
        if request.method != "POST" or not self.has_change_permission(request):
            raise PermissionDenied
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
        context = {**(extra_context or {}), "mail_state": mail_state(), "not_configured": NOT_CONFIGURED}
        response: HttpResponse = super().changelist_view(request, context)
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
