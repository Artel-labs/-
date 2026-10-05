from axes.models import AccessAttempt, AccessLog


class Lockout(AccessAttempt):
    class Meta:
        proxy = True
        verbose_name = "блокировка"
        verbose_name_plural = "Блокировки"


class LoginJournal(AccessLog):
    class Meta:
        proxy = True
        verbose_name = "запись журнала входов"
        verbose_name_plural = "Журнал входов"
