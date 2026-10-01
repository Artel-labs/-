from django.conf import settings
from django.db import models


class TwoFactor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="two_factor")
    secret = models.CharField("Секрет", max_length=64)
    confirmed_at = models.DateTimeField("Включён", null=True, blank=True)
    last_step = models.BigIntegerField("Последний принятый шаг", default=0)

    class Meta:
        verbose_name = "двухфакторный вход"
        verbose_name_plural = "Двухфакторный вход"

    def __str__(self) -> str:
        return f"Двухфакторный вход: {self.user}"

    @property
    def enabled(self) -> bool:
        return self.confirmed_at is not None
