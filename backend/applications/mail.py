import smtplib

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from applications.delivery import schedule_retry
from applications.models import ApplicantType, Application, MailStatus, Topic
from applications.recipients import all_recipients, recipients_for
from applications.topics import is_anonymous

SUBJECT_TOPICS = {
    Topic.PROGRAM: "Заявка ДПО",
    Topic.COURSE_IDEA: "Идея курса",
    Topic.TEACHING: "Заявка преподавателя",
    Topic.FEEDBACK: "Отзыв о работе центра",
}
ANONYMOUS_SUBJECTS = {Topic.COURSE_IDEA: "Идея курса", Topic.FEEDBACK: "Отзыв"}
ANONYMOUS_LINE = "Обращение анонимное: контактов заявителя нет."
AUTO_SENT = "Письмо отправлено сайтом Центра ДПО факультета права автоматически, отвечать на него не нужно"
MAX_ERROR_LENGTH = 500
TEST_SUBJECT = "Проверка почты · Центр ДПО факультета права"
NO_SMTP = "Почтовый сервер не настроен: укажите SMTP_HOST в файле .env на сервере."
RECIPIENTS_PLACE = "добавьте их в админке: «Заявки» → «Получатели писем»."


def no_recipients(topic: str) -> str:
    return f"Нет получателей для темы «{Topic(topic).label}»: {RECIPIENTS_PLACE}"


def skip_reason(topic: str) -> str:
    if not settings.EMAIL_HOST:
        return NO_SMTP
    return "" if recipients_for(topic) else no_recipients(topic)


def test_mail_problem() -> str:
    if not settings.EMAIL_HOST:
        return NO_SMTP
    return "" if all_recipients() else f"Нет активных получателей писем: {RECIPIENTS_PLACE}"


def moscow_time(application: Application) -> str:
    return timezone.localtime(application.received_at).strftime("%d.%m.%Y, %H:%M:%S")


def subject(application: Application) -> str:
    if is_anonymous(application.topic):
        return f"{ANONYMOUS_SUBJECTS[Topic(application.topic)]} № {application.pk}"
    corporate = (
        f" ({ApplicantType.CORPORATE.label.lower()})" if application.applicant_type == ApplicantType.CORPORATE else ""
    )
    topic = SUBJECT_TOPICS.get(Topic(application.topic), application.topic)
    if application.topic == Topic.PROGRAM:
        return f"{topic}{corporate}: {application.full_name} — {application.program_title or 'без программы'}"
    return f"{topic}{corporate}: {application.full_name}"


def applicant_field() -> str:
    return str(Application._meta.get_field("applicant_type").verbose_name)


def company_field() -> str:
    return str(Application._meta.get_field("company").verbose_name)


def corporate_lines(application: Application) -> list[str]:
    if application.applicant_type != ApplicantType.CORPORATE:
        return []
    lines = ["", f"{applicant_field()}: {ApplicantType.CORPORATE.label.lower()} (корпоративное обучение)."]
    if application.company:
        lines.append(f"{company_field()}: {application.company}")
    if application.employees_count:
        lines.append(f"Сотрудников к обучению: {application.employees_count}")
    if application.timeframe:
        lines.append(f"Желаемые сроки: {application.timeframe}")
    return lines


def heading(application: Application) -> str:
    if application.topic == Topic.PROGRAM:
        return f"Заявка на программу: {application.program_title or 'программа не указана'}"
    return f"Тема обращения: {SUBJECT_TOPICS.get(Topic(application.topic), application.topic)}"


def applicant_lines(application: Application) -> list[str]:
    if is_anonymous(application.topic):
        return [ANONYMOUS_LINE]
    return [
        f"Имя и фамилия: {application.full_name}",
        f"Телефон:       {application.phone}",
        f"Почта:         {application.email}",
        *corporate_lines(application),
        "",
        "Анонсы новых программ получать ОТКАЗАЛСЯ(ЛАСЬ)."
        if application.no_announcements
        else "Согласен(на) получать анонсы новых программ.",
    ]


def footer_lines(application: Application) -> list[str]:
    if is_anonymous(application.topic):
        return [f"{AUTO_SENT}."]
    return [
        "Согласие на обработку персональных данных получено вместе с заявкой.",
        f"{AUTO_SENT} —",
        "чтобы ответить заявителю, пишите на адрес из поля «Почта».",
    ]


def letter(application: Application) -> str:
    lines = [heading(application), "", *applicant_lines(application)]
    if application.comment:
        lines += ["", "Комментарий:", application.comment]
    if application.program:
        lines += ["", f"Страница программы: {settings.SITE_URL}/{application.program.path}"]
    lines += [
        "",
        "— — —",
        f"Заявка № {application.pk}",
        f"Получена: {moscow_time(application)} (Москва)",
        *footer_lines(application),
    ]
    return "\n".join(lines)


def failure_text(error: Exception, attempt: int) -> str:
    retry = attempt < settings.APPLICATION_MAIL_ATTEMPTS
    tail = (
        f" Повтор через {settings.APPLICATION_MAIL_RETRY_MINUTES} мин."
        if retry
        else " Автоматические повторы закончились."
    )
    return f"Попытка {attempt}: {error}"[: MAX_ERROR_LENGTH - len(tail)] + tail


def mark(application_id: int, status: MailStatus, error: str = "", **extra: int) -> None:
    Application.objects.filter(pk=application_id).update(mail_status=status, mail_error=error, **extra)


def send_application_mail(application_id: int) -> str:
    application = Application.objects.select_related("program").get(pk=application_id)
    reason = skip_reason(application.topic)
    if reason:
        mark(application_id, MailStatus.SKIPPED, reason)
        return reason
    attempt = application.mail_attempts + 1
    message = EmailMessage(
        subject=subject(application),
        body=letter(application),
        to=recipients_for(application.topic),
        reply_to=[] if is_anonymous(application.topic) else [application.email],
    )
    try:
        message.send()
    except (smtplib.SMTPException, OSError) as error:
        mark(application_id, MailStatus.FAILED, failure_text(error, attempt), mail_attempts=attempt)
        if attempt < settings.APPLICATION_MAIL_ATTEMPTS:
            schedule_retry(application_id, attempt + 1)
        raise
    mark(application_id, MailStatus.SENT, mail_attempts=attempt)
    return f"Письмо по заявке № {application_id} отправлено"


def send_test_mail() -> None:
    EmailMessage(
        subject=TEST_SUBJECT,
        body=(
            "Это пробное письмо из админки Центра ДПО факультета права.\n"
            "Если вы его видите, доставка заявок на этот адрес работает.\n\n"
            f"Отправлено: {timezone.localtime().strftime('%d.%m.%Y, %H:%M:%S')} (Москва)."
        ),
        to=all_recipients(),
    ).send()
