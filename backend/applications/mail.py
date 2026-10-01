import smtplib

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from applications.models import ApplicantType, Application, MailStatus, Source, Topic

SUBJECT_TOPICS = {
    Topic.PROGRAM: "Заявка ДПО",
    Topic.COURSE_IDEA: "Идея курса",
    Topic.TEACHING: "Заявка преподавателя",
    Topic.FEEDBACK: "Отзыв о работе центра",
}
MAX_ERROR_LENGTH = 500
TEST_SUBJECT = "Проверка почты · Центр ДПО факультета права"


def mail_configured() -> bool:
    return bool(settings.EMAIL_HOST and settings.APPLICATION_MAIL_TO)


def moscow_time(application: Application) -> str:
    return timezone.localtime(application.received_at).strftime("%d.%m.%Y, %H:%M:%S")


def subject(application: Application) -> str:
    corporate = " (от организации)" if application.applicant_type == ApplicantType.CORPORATE else ""
    topic = SUBJECT_TOPICS.get(Topic(application.topic), application.topic)
    if application.topic == Topic.PROGRAM:
        return f"{topic}{corporate}: {application.full_name} — {application.program_title or 'без программы'}"
    return f"{topic}{corporate}: {application.full_name}"


def source_label(source: str, other: str) -> str:
    label = Source(source).label
    return f"{label}: {other}" if source == Source.OTHER and other else label


def source_labels(application: Application) -> list[str]:
    return [source_label(source, application.source_other) for source in application.sources]


def corporate_lines(application: Application) -> list[str]:
    if application.applicant_type != ApplicantType.CORPORATE:
        return []
    lines = ["", "Заявка ОТ ОРГАНИЗАЦИИ (корпоративное обучение)."]
    if application.employees_count:
        lines.append(f"Сотрудников к обучению: {application.employees_count}")
    if application.timeframe:
        lines.append(f"Желаемые сроки: {application.timeframe}")
    return lines


def heading(application: Application) -> str:
    if application.topic == Topic.PROGRAM:
        return f"Заявка на программу: {application.program_title or 'программа не указана'}"
    return f"Тема обращения: {SUBJECT_TOPICS.get(Topic(application.topic), application.topic)}"


def letter(application: Application) -> str:
    lines = [
        heading(application),
        "",
        f"Имя и фамилия: {application.full_name}",
        f"Телефон:       {application.phone}",
        f"Почта:         {application.email}",
    ]
    if application.position:
        lines.append(f"Должность:     {application.position}")
    if application.company:
        lines.append(f"Место работы:  {application.company}")
    lines += [*corporate_lines(application), ""]
    sources = source_labels(application)
    if sources:
        lines.append(f"Узнал(а) о нас: {', '.join(sources)}")
    lines.append(
        "Анонсы новых программ получать ОТКАЗАЛСЯ(ЛАСЬ)."
        if application.no_announcements
        else "Согласен(на) получать анонсы новых программ."
    )
    if application.comment:
        lines += ["", "Комментарий:", application.comment]
    if application.program:
        lines += ["", f"Страница программы: {settings.SITE_URL}/{application.program.path}"]
    lines += [
        "",
        "— — —",
        f"Заявка № {application.pk}",
        f"Получена: {moscow_time(application)} (Москва)",
        "Согласие на обработку персональных данных получено вместе с заявкой.",
        "Письмо отправлено сайтом Центра ДПО факультета права автоматически, отвечать на него не нужно —",
        "чтобы ответить заявителю, пишите на адрес из поля «Почта».",
    ]
    return "\n".join(lines)


def send_application_mail(application_id: int) -> str:
    application = Application.objects.select_related("program").get(pk=application_id)
    message = EmailMessage(
        subject=subject(application),
        body=letter(application),
        to=settings.APPLICATION_MAIL_TO,
        reply_to=[application.email],
    )
    try:
        message.send()
    except (smtplib.SMTPException, OSError) as error:
        Application.objects.filter(pk=application_id).update(
            mail_status=MailStatus.FAILED, mail_error=str(error)[:MAX_ERROR_LENGTH]
        )
        raise
    Application.objects.filter(pk=application_id).update(mail_status=MailStatus.SENT, mail_error="")
    return f"Письмо по заявке № {application_id} отправлено"


def send_test_mail() -> None:
    EmailMessage(
        subject=TEST_SUBJECT,
        body=(
            "Это пробное письмо из админки Центра ДПО факультета права.\n"
            "Если вы его видите, доставка заявок на этот адрес работает.\n\n"
            f"Отправлено: {timezone.localtime().strftime('%d.%m.%Y, %H:%M:%S')} (Москва)."
        ),
        to=settings.APPLICATION_MAIL_TO,
    ).send()
