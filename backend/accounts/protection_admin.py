from axes.admin import AccessAttemptAdmin, AccessFailureLogAdmin, AccessLogAdmin
from axes.models import AccessAttempt, AccessFailureLog, AccessLog
from django.contrib import admin
from unfold.admin import ModelAdmin

from core.admin_tools import ViewOnly, take_over

take_over(AccessAttempt, AccessLog, AccessFailureLog)


@admin.register(AccessAttempt)
class LoginAttemptAdmin(ViewOnly, AccessAttemptAdmin, ModelAdmin):
    pass


@admin.register(AccessLog)
class LoginLogAdmin(ViewOnly, AccessLogAdmin, ModelAdmin):
    pass


@admin.register(AccessFailureLog)
class LoginFailureAdmin(ViewOnly, AccessFailureLogAdmin, ModelAdmin):
    pass
