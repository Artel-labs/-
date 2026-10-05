from django.contrib import admin
from django_q.admin import FailAdmin, QueueAdmin, ScheduleAdmin, TaskAdmin
from django_q.models import Failure, OrmQ, Schedule, Success
from unfold.admin import ModelAdmin

from core.admin_tools import ViewOnly, take_over

take_over(Schedule, Success, Failure, OrmQ)


@admin.register(Schedule)
class BackgroundScheduleAdmin(ScheduleAdmin, ModelAdmin):
    pass


@admin.register(Success)
class SuccessfulTaskAdmin(ViewOnly, TaskAdmin, ModelAdmin):
    pass


@admin.register(Failure)
class FailedTaskAdmin(ViewOnly, FailAdmin, ModelAdmin):
    pass


@admin.register(OrmQ)
class QueuedTaskAdmin(QueueAdmin, ModelAdmin):
    pass
