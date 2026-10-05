from collections.abc import Callable
from typing import Any

from axes.utils import reset as reset_lockout
from django import forms
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from unfold.admin import ModelAdmin
from unfold.decorators import action, display
from unfold.widgets import UnfoldAdminRadioSelectWidget

from accounts import two_factor
from accounts.passwords import new_password
from accounts.roles import ROLE_HELP, Role, apply_role, role_of
from accounts.staff_rules import protected_reason
from accounts.staff_state import has_two_factor, is_locked
from core.steps import Step, Subject, page_context, run_step

ISSUED_TEMPLATE = "admin/auth/user/issued.html"
CREATED_TITLE = "Сотрудник добавлен"
RESET_TITLE = "Новый пароль"
EMPTY = "—"

admin.site.unregister(User)
admin.site.unregister(Group)


STEPS = {
    "reset_password": Step(
        "Сбросить пароль?",
        "Старый пароль перестанет работать. Новый пароль появится на следующем экране один раз.",
        "Сбросить пароль",
        False,
    ),
    "disable_access": Step(
        "Отключить доступ?",
        "Сотрудник не сможет войти в админку. Учётная запись и история сохранятся, доступ можно вернуть.",
        "Отключить доступ",
        True,
        "Доступ отключён.",
    ),
    "enable_access": Step(
        "Включить доступ?",
        "Сотрудник снова сможет входить в админку со своим паролем.",
        "Включить доступ",
        False,
        "Доступ включён.",
    ),
    "drop_two_factor": Step(
        "Отключить двухфакторный вход?",
        "Для входа будет достаточно пароля. Сотрудник сможет снова включить защиту в меню «Двухфакторный вход».",
        "Отключить двухфакторный вход",
        True,
        "Двухфакторный вход отключён.",
    ),
    "unlock": Step(
        "Снять блокировку входа?",
        "Сотрудник сможет сразу снова попробовать войти.",
        "Снять блокировку",
        False,
        "Блокировка входа снята.",
    ),
}


class StaffForm(forms.ModelForm):
    actor: User | AnonymousUser | None = None
    role = forms.ChoiceField(
        label="Роль",
        choices=Role.choices,
        initial=Role.STAFF,
        widget=UnfoldAdminRadioSelectWidget,
        help_text=ROLE_HELP,
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        labels = {"username": "Логин", "first_name": "Имя", "last_name": "Фамилия", "email": "Почта"}
        help_texts = {"username": "Латинские буквы, цифры и символы @ . + - _"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role"].initial = role_of(self.instance)

    def clean_role(self) -> str:
        role = str(self.cleaned_data["role"])
        demoted = bool(self.instance.pk) and role == Role.STAFF and role_of(self.instance) == Role.ADMIN
        reason = protected_reason(self.actor, self.instance) if demoted and self.actor else None
        if reason:
            raise forms.ValidationError(reason)
        return role


class RoleFilter(admin.SimpleListFilter):
    title = "Роль"
    parameter_name = "role"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return list(Role.choices)

    def queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> QuerySet[User]:
        if self.value() is None:
            return queryset
        return queryset.filter(is_superuser=self.value() == Role.ADMIN)


def user_by_id(object_id: Any) -> User | None:
    return User.objects.filter(pk=object_id).first()


@admin.register(User)
class StaffAdmin(ModelAdmin):
    form = StaffForm
    list_display = ["display_name", "login", "role_label", "access", "two_factor_state", "last_login"]
    list_display_links = ["display_name", "login"]
    list_filter = [RoleFilter, "is_active"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering = ["username"]
    actions_detail = ["reset_password", "disable_access", "enable_access", "drop_two_factor", "unlock"]
    state_fields = ["access_state", "last_login", "date_joined", "two_factor_state", "lock_state"]
    main_fields = ["username", "first_name", "last_name", "email", "role"]

    def get_fieldsets(self, request: HttpRequest, obj: User | None = None) -> Any:
        main = ("Сотрудник", {"fields": self.main_fields})
        return [main] if obj is None else [main, ("Состояние входа", {"fields": self.state_fields})]

    def get_readonly_fields(self, request: HttpRequest, obj: User | None = None) -> Any:
        return [] if obj is None else self.state_fields

    def get_form(self, request: HttpRequest, obj: Any = None, change: bool = False, **kwargs: Any) -> Any:
        form = super().get_form(request, obj, change=change, **kwargs)
        return type(form.__name__, (form,), {"actor": request.user})

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        return {}

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        allowed = super().has_delete_permission(request, obj)
        return bool(allowed and (obj is None or protected_reason(request.user, obj) is None))

    def save_model(self, request: HttpRequest, obj: User, form: Any, change: bool) -> None:
        if not change:
            obj.set_unusable_password()
            obj.is_staff = True
        super().save_model(request, obj, form, change)
        apply_role(obj, form.cleaned_data["role"])

    def response_add(self, request: HttpRequest, obj: User, post_url_continue: Any = None) -> HttpResponse:
        return self.password_page(request, obj, CREATED_TITLE)

    @display(description="Имя и фамилия", ordering="last_name")
    def display_name(self, user: User) -> str:
        return user.get_full_name() or EMPTY

    @display(description="Логин", ordering="username")
    def login(self, user: User) -> str:
        return user.get_username()

    @display(description="Роль")
    def role_label(self, user: User) -> str:
        return str(role_of(user).label)

    @display(description="Доступ", boolean=True, ordering="is_active")
    def access(self, user: User) -> bool:
        return user.is_active

    @display(description="Доступ")
    def access_state(self, user: User) -> str:
        return "Включён" if user.is_active else "Отключён"

    @display(description="Двухфакторный вход", boolean=True)
    def two_factor_state(self, user: User) -> bool:
        return has_two_factor(user)

    @display(description="Блокировка входа")
    def lock_state(self, user: User) -> str:
        return "Заблокирован после неверных попыток" if is_locked(user) else "Нет"

    def target_allows(self, request: HttpRequest, object_id: Any, check: Callable[[User], bool]) -> bool:
        target = user_by_id(object_id)
        return bool(self.has_change_permission(request) and target and check(target))

    def has_reset_password_permission(self, request: HttpRequest, object_id: Any = None) -> bool:
        return self.target_allows(request, object_id, lambda target: True)

    def has_disable_access_permission(self, request: HttpRequest, object_id: Any = None) -> bool:
        return self.target_allows(
            request, object_id, lambda target: target.is_active and protected_reason(request.user, target) is None
        )

    def has_enable_access_permission(self, request: HttpRequest, object_id: Any = None) -> bool:
        return self.target_allows(request, object_id, lambda target: not target.is_active)

    def has_drop_two_factor_permission(self, request: HttpRequest, object_id: Any = None) -> bool:
        return self.target_allows(request, object_id, has_two_factor)

    def has_unlock_permission(self, request: HttpRequest, object_id: Any = None) -> bool:
        return self.target_allows(request, object_id, is_locked)

    @action(description="Сбросить пароль", url_path="reset-password", icon="key", permissions=["reset_password"])
    def reset_password(self, request: HttpRequest, object_id: Any) -> HttpResponse:
        return self.run_step(request, object_id, "reset_password", self.after_reset)

    @action(description="Отключить доступ", url_path="disable-access", icon="block", permissions=["disable_access"])
    def disable_access(self, request: HttpRequest, object_id: Any) -> HttpResponse:
        return self.run_step(request, object_id, "disable_access", lambda _, target: self.set_active(target, False))

    @action(description="Включить доступ", url_path="enable-access", icon="check_circle", permissions=["enable_access"])
    def enable_access(self, request: HttpRequest, object_id: Any) -> HttpResponse:
        return self.run_step(request, object_id, "enable_access", lambda _, target: self.set_active(target, True))

    @action(
        description="Отключить двухфакторный вход",
        url_path="drop-two-factor",
        icon="phonelink_erase",
        permissions=["drop_two_factor"],
    )
    def drop_two_factor(self, request: HttpRequest, object_id: Any) -> HttpResponse:
        return self.run_step(request, object_id, "drop_two_factor", lambda _, target: two_factor.reset(target))

    @action(description="Снять блокировку входа", url_path="unlock", icon="lock_open", permissions=["unlock"])
    def unlock(self, request: HttpRequest, object_id: Any) -> HttpResponse:
        return self.run_step(
            request, object_id, "unlock", lambda _, target: reset_lockout(username=target.get_username())
        )

    def run_step(
        self, request: HttpRequest, object_id: Any, name: str, perform: Callable[[HttpRequest, User], Any]
    ) -> HttpResponse:
        target = get_object_or_404(User, pk=object_id)
        if not getattr(self, f"has_{name}_permission")(request, object_id):
            raise PermissionDenied
        subject = Subject("Сотрудник", f"{target.get_full_name() or target.get_username()} ({target.get_username()})")
        return run_step(self, request, STEPS[name], subject, self.card_url(target), lambda: perform(request, target))

    def after_reset(self, request: HttpRequest, target: User) -> HttpResponse:
        return self.password_page(request, target, RESET_TITLE)

    def set_active(self, target: User, active: bool) -> None:
        target.is_active = active
        target.save(update_fields=["is_active"])

    def card_url(self, target: User) -> str:
        return reverse("admin:auth_user_change", args=[target.pk])

    def password_page(self, request: HttpRequest, target: User, title: str) -> TemplateResponse:
        password = new_password(target)
        target.set_password(password)
        target.save(update_fields=["password"])
        context = {**page_context(self, request, title, self.card_url(target)), "target": target, "password": password}
        response = TemplateResponse(request, ISSUED_TEMPLATE, context)
        add_never_cache_headers(response)
        return response
