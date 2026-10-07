from django.conf import settings
from django.db import models

from accounts.secret_box import seal, unseal


class TwoFactor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="two_factor")
    sealed_secret = models.CharField("Секрет (зашифрован)", max_length=255)
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

    @property
    def secret(self) -> str:
        return unseal(self.sealed_secret)

    @secret.setter
    def secret(self, value: str) -> None:
        self.sealed_secret = seal(value)
