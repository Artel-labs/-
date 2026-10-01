from django.contrib import admin
from django_q.admin import FailAdmin, QueueAdmin, ScheduleAdmin, TaskAdmin
from django_q.models import Failure, OrmQ, Schedule, Success
from unfold.admin import ModelAdmin

for model in (Schedule, Success, Failure, OrmQ):
    if admin.site.is_registered(model):
        admin.site.unregister(model)


@admin.register(Schedule)
class BackgroundScheduleAdmin(ScheduleAdmin, ModelAdmin):
    pass


@admin.register(Success)
class SuccessfulTaskAdmin(TaskAdmin, ModelAdmin):
    pass


@admin.register(Failure)
class FailedTaskAdmin(FailAdmin, ModelAdmin):
    pass


@admin.register(OrmQ)
class QueuedTaskAdmin(QueueAdmin, ModelAdmin):
    pass
