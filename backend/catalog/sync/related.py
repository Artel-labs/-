from catalog.hse.details import FileData, ProgramDetails
from catalog.models import FaqItem, Module, Program, ProgramFile, ProgramTeacher, Review, Teacher
from catalog.sync.fields import lines
from catalog.teachers import canonical_name


def replace_modules(program: Program, details: ProgramDetails) -> None:
    if not details.modules:
        return
    program.modules.all().delete()
    Module.objects.bulk_create(
        Module(program=program, title=item.title, hours=item.hours, topics=lines(item.topics), position=position)
        for position, item in enumerate(details.modules)
    )


def replace_faq(program: Program, details: ProgramDetails) -> None:
    if not details.faq:
        return
    program.faq.all().delete()
    FaqItem.objects.bulk_create(
        FaqItem(program=program, question=item.question, answer=item.answer, position=position)
        for position, item in enumerate(details.faq)
    )


def replace_reviews(program: Program, details: ProgramDetails) -> None:
    if not details.reviews:
        return
    program.reviews.all().delete()
    Review.objects.bulk_create(
        Review(program=program, text=item.text, author=item.author, position=position)
        for position, item in enumerate(details.reviews)
    )


def replace_teachers(program: Program, details: ProgramDetails) -> list[Teacher]:
    if not details.teachers:
        return []
    program.program_teachers.all().delete()
    teachers = []
    for position, item in enumerate(details.teachers):
        teacher, _ = Teacher.objects.get_or_create(name=canonical_name(item.name))
        ProgramTeacher.objects.create(program=program, teacher=teacher, about=item.about, position=position)
        teachers.append(teacher)
    return teachers


def sync_file(program: Program, item: FileData, position: int) -> ProgramFile:
    document = program.files.filter(kind=item.kind).first() or ProgramFile(program=program, kind=item.kind)
    document.title = item.title
    document.size_label = item.size
    document.source_url = item.url
    document.position = position
    document.save()
    return document


def replace_files(program: Program, details: ProgramDetails) -> list[ProgramFile]:
    if not details.files:
        return []
    documents = [sync_file(program, item, position) for position, item in enumerate(details.files)]
    for stale in program.files.exclude(pk__in=[document.pk for document in documents]):
        stale.file.delete(save=False)
        stale.delete()
    return documents


def replace_related(program: Program, details: ProgramDetails) -> tuple[list[Teacher], list[ProgramFile]]:
    replace_modules(program, details)
    replace_faq(program, details)
    replace_reviews(program, details)
    return replace_teachers(program, details), replace_files(program, details)
