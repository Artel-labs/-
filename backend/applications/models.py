from django.db import models
from django.utils import timezone

from catalog.models import Program

ANONYMOUS = "Анонимно"


class Topic(models.TextChoices):
    PROGRAM = "program", "Заявка на программу"
    COURSE_IDEA = "course-idea", "Идея курса"
    TEACHING = "teaching", "Хочу стать преподавателем"
    FEEDBACK = "feedback", "Отзыв о работе центра"


class ApplicantType(models.TextChoices):
    PERSONAL = "personal", "Частное лицо"
    CORPORATE = "corporate", "Сотрудник организации"


class Status(models.TextChoices):
    NEW = "new", "Новая"
    IN_PROGRESS = "in-progress", "В работе"
    DONE = "done", "Обработана"
    REJECTED = "rejected", "Отклонена"


CLOSED_STATUSES = (Status.DONE, Status.REJECTED)


class MailStatus(models.TextChoices):
    QUEUED = "queued", "Отправляется"
    SENT = "sent", "Отправлено"
    FAILED = "failed", "Не отправлено"
    SKIPPED = "skipped", "Почта не настроена"


class Application(models.Model):
    received_at = models.DateTimeField("Получена", default=timezone.now, db_index=True)
    topic = models.CharField("Тема", max_length=20, choices=Topic.choices, default=Topic.PROGRAM)
    applicant_type = models.CharField(
        "Кто будет обучаться",
        max_length=20,
        choices=ApplicantType.choices,
        default=ApplicantType.PERSONAL,
        blank=True,
        help_text="Только для заявки на программу",
    )
    employees_count = models.CharField("Сотрудников к обучению", max_length=40, blank=True)
    timeframe = models.CharField("Желаемые сроки", max_length=200, blank=True)
    first_name = models.CharField("Имя", max_length=80, blank=True)
    last_name = models.CharField("Фамилия", max_length=80, blank=True)
    phone = models.CharField("Телефон", max_length=40, blank=True)
    email = models.EmailField("Почта", max_length=160, blank=True)
    company = models.CharField(
        "Организация-заказчик", max_length=160, blank=True, help_text="Только для корпоративной заявки"
    )
    comment = models.TextField("Комментарий", max_length=1000, blank=True)
    consent_at = models.DateTimeField("Согласие на обработку ПДн дано", null=True, blank=True, editable=False)
    consent_version = models.CharField("Версия текста согласия", max_length=40, blank=True, editable=False)
    ads_consent_at = models.DateTimeField("Согласие на рассылки дано", null=True, blank=True, editable=False)
    ads_consent_version = models.CharField(
        "Версия текста согласия на рассылки", max_length=40, blank=True, editable=False
    )
    ads_consent_withdrawn_at = models.DateTimeField(
        "Согласие на рассылки отозвано", null=True, blank=True, editable=False
    )
    program = models.ForeignKey(
        Program, verbose_name="Программа", null=True, blank=True, on_delete=models.SET_NULL, related_name="applications"
    )
    program_title = models.CharField("Название программы", max_length=300, blank=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    closed_at = models.DateTimeField("Рассмотрена", null=True, blank=True, editable=False)
    mail_status = models.CharField("Письмо", max_length=20, choices=MailStatus.choices, default=MailStatus.QUEUED)
    mail_error = models.CharField("Ошибка письма", max_length=500, blank=True)
    mail_attempts = models.PositiveSmallIntegerField("Попыток отправки", default=0)
    duplicate_key = models.CharField(max_length=300, db_index=True, editable=False)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self) -> str:
        return f"№ {self.pk} · {self.full_name}"

    @property
    def full_name(self) -> str:
        return " ".join(part for part in (self.last_name, self.first_name) if part) or ANONYMOUS


def all_topics() -> list[str]:
    return list(Topic.values)


class MailRecipient(models.Model):
    email = models.EmailField("Адрес", max_length=160, unique=True)
    topics = models.JSONField("Темы заявок", default=all_topics)
    is_active = models.BooleanField("Получает письма", default=True)
    note = models.CharField("Кто это", max_length=120, blank=True)

    class Meta:
        ordering = ["email"]
        verbose_name = "получатель писем"
        verbose_name_plural = "Получатели писем"

    def __str__(self) -> str:
        return self.email
