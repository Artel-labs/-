from django.db import models


class EventType(models.TextChoices):
    PAGEVIEW = "pageview", "Просмотр страницы"
    HEARTBEAT = "heartbeat", "Время на странице"
    CLICK = "click", "Переход по сайту"
    OUTBOUND = "outbound", "Переход на другой сайт"
    PROGRAM = "program", "Переход к программе"
    FILTER = "filter", "Фильтр каталога"
    SCROLL = "scroll", "Прокрутка"
    EXIT = "exit", "Уход со страницы"
    FORM_ERROR = "form_error", "Ошибка отправки заявки"


class Device(models.TextChoices):
    MOBILE = "mobile", "Телефон"
    TABLET = "tablet", "Планшет"
    DESKTOP = "desktop", "Компьютер"


class Event(models.Model):
    occurred_at = models.DateTimeField("Время", db_index=True)
    session = models.CharField("Сессия", max_length=64, db_index=True)
    type = models.CharField("Тип", max_length=16, choices=EventType.choices)
    path = models.CharField("Страница", max_length=300)
    title = models.CharField("Заголовок", max_length=200, blank=True)
    referrer = models.CharField("Источник", max_length=200, blank=True)
    target = models.CharField("Цель", max_length=500, blank=True)
    label = models.CharField("Подпись", max_length=120, blank=True)
    duration_ms = models.PositiveIntegerField("Время, мс", default=0)
    device = models.CharField("Устройство", max_length=8, choices=Device.choices)
    language = models.CharField("Язык", max_length=16, blank=True)
    scroll = models.PositiveSmallIntegerField("Прокрутка, %", default=0)

    class Meta:
        verbose_name = "событие"
        verbose_name_plural = "Посещаемость"
        ordering = ["-occurred_at"]

    def __str__(self) -> str:
        return f"{self.get_type_display()} · {self.path}"
