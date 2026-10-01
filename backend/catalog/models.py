from django.db import models

from catalog.slugs import program_path


class Source(models.TextChoices):
    HSE = "hse", "Сайт НИУ ВШЭ"
    MANUAL = "manual", "Вручную"


class FileKind(models.TextChoices):
    PLAN = "plan", "Учебный план"
    SCHEDULE = "schedule", "Расписание"


class Sphere(models.Model):
    slug = models.SlugField("Код", unique=True)
    title = models.CharField("Название", max_length=200)
    position = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Направление"
        verbose_name_plural = "Направления"

    def __str__(self) -> str:
        return self.title


class Teacher(models.Model):
    name = models.CharField("ФИО", max_length=200, unique=True)
    photo = models.ImageField("Фото", upload_to="teachers/", blank=True)
    page_url = models.URLField("Страница на hse.ru", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"

    def __str__(self) -> str:
        return self.name


class Program(models.Model):
    hse_id = models.CharField("Код на hse.ru", max_length=32, unique=True)
    title = models.CharField("Название", max_length=300)
    sphere = models.ForeignKey(
        Sphere, verbose_name="Направление", null=True, blank=True, on_delete=models.SET_NULL, related_name="programs"
    )
    position = models.PositiveSmallIntegerField("Порядок в направлении", default=0)
    is_published = models.BooleanField("Показывать на сайте", default=True)
    source = models.CharField("Источник", max_length=10, choices=Source.choices, default=Source.MANUAL)
    locked = models.BooleanField(
        "Не обновлять с hse.ru", default=False, help_text="Ручные правки сохранятся при обновлении каталога"
    )
    hse_url = models.URLField("Страница на hse.ru", blank=True)
    type_short = models.CharField("Тип (кратко)", max_length=20, help_text="ПК или ПП")
    type_title = models.CharField("Тип", max_length=100)
    study_format = models.CharField("Формат", max_length=200)
    duration = models.CharField("Длительность", max_length=100, blank=True)
    hours = models.CharField("Объём", max_length=100, blank=True)
    language = models.CharField("Язык", max_length=100, blank=True)
    schedule = models.CharField("График занятий", max_length=300, blank=True)
    start_date = models.DateField("Старт", null=True, blank=True)
    start_month_only = models.BooleanField("Известен только месяц старта", default=False)
    price = models.PositiveIntegerField("Цена со скидкой, ₽", null=True, blank=True)
    base_price = models.PositiveIntegerField("Цена, ₽", null=True, blank=True)
    tax_refund = models.CharField("Налоговый вычет", max_length=100, blank=True)
    tagline = models.TextField("Короткое описание", blank=True)
    about = models.TextField("О программе", blank=True)
    audience_intro = models.TextField("Кому подойдёт: вступление", blank=True)
    audience = models.TextField("Кому подойдёт", blank=True, help_text="По одному пункту на строку")
    results = models.TextField("Чему научитесь", blank=True, help_text="По одному пункту на строку")
    advantages = models.TextField("Преимущества", blank=True, help_text="По одному пункту на строку")
    discounts = models.TextField("Скидки", blank=True, help_text="По одному пункту на строку")
    admission_documents = models.TextField("Документы для приёма", blank=True, help_text="По одному пункту на строку")
    image = models.ImageField("Обложка", upload_to="programs/", blank=True)
    notice_date = models.CharField("Объявление: дата", max_length=20, blank=True)
    notice_text = models.TextField("Объявление: текст", blank=True)
    notice_url = models.URLField("Объявление: ссылка", max_length=500, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        ordering = ["sphere__position", "position", "title"]
        verbose_name = "Программа"
        verbose_name_plural = "Программы"

    def __str__(self) -> str:
        return self.title

    @property
    def path(self) -> str:
        return program_path(self.title, self.hse_id)


class Module(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField("Название", max_length=500)
    hours = models.CharField("Часы", max_length=50, blank=True)
    topics = models.TextField("Темы", blank=True, help_text="По одной теме на строку")
    position = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Модуль"
        verbose_name_plural = "Программа обучения"

    def __str__(self) -> str:
        return self.title


class FaqItem(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="faq")
    question = models.CharField("Вопрос", max_length=500)
    answer = models.TextField("Ответ")
    position = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Вопрос"
        verbose_name_plural = "Частые вопросы"

    def __str__(self) -> str:
        return self.question


class Review(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="reviews")
    text = models.TextField("Отзыв")
    author = models.CharField("Автор", max_length=200, blank=True)
    position = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self) -> str:
        return self.author or self.text[:50]


class ProgramFile(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="files")
    kind = models.CharField("Вид", max_length=20, choices=FileKind.choices)
    title = models.CharField("Название", max_length=300)
    size_label = models.CharField("Размер", max_length=50, blank=True)
    source_url = models.URLField("Ссылка на hse.ru", max_length=500, blank=True)
    file = models.FileField("Файл", upload_to="files/", blank=True)
    position = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Документ"
        verbose_name_plural = "Документы программы"

    def __str__(self) -> str:
        return self.title


class ProgramTeacher(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="program_teachers")
    teacher = models.ForeignKey(Teacher, verbose_name="Преподаватель", on_delete=models.PROTECT, related_name="roles")
    about = models.TextField("Должность и регалии", blank=True)
    position = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["position"]
        verbose_name = "Преподаватель программы"
        verbose_name_plural = "Преподаватели программы"
        constraints = [models.UniqueConstraint(fields=["program", "teacher"], name="unique_program_teacher")]

    def __str__(self) -> str:
        return self.teacher.name
