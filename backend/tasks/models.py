from django_q.models import Schedule, Task


class PlannedTask(Schedule):
    class Meta:
        proxy = True
        verbose_name = "задача по расписанию"
        verbose_name_plural = "Расписание"


class TaskRecord(Task):
    class Meta:
        proxy = True
        verbose_name = "запись журнала задач"
        verbose_name_plural = "Журнал задач"
