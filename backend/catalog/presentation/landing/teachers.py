import json
import re
from dataclasses import dataclass, field

from catalog.hse.client import is_hse_url
from catalog.landing_schemas import TeacherCardOut, TeacherPhotoOut
from catalog.models import Program, Teacher
from catalog.presentation.images import Photo, photo_with_webp
from catalog.presentation.landing.collation import sort_key
from catalog.presentation.text import plural_programs

MAX_ALT_LENGTH = 125
MIN_TOKEN_LENGTH = 2
TODO_MARK = re.compile(r"\btodo\b", re.IGNORECASE)
TEXT_FIXES = (("внешнеэкономический деятельности", "внешнеэкономической деятельности"),)
TEACHER_ABOUT = {
    "Максимов Дмитрий Михайлович": "Старший преподаватель департамента правового регулирования бизнеса НИУ ВШЭ",
    "Дмитрий Максимов": "Старший преподаватель департамента правового регулирования бизнеса НИУ ВШЭ",
    "Жирнова Наталья Александровна": (
        "Доцент, научный сотрудник департамента права цифровых технологий и биоправа НИУ ВШЭ, кандидат юридических наук"
    ),
    "Журавлев Михаил Сергеевич": (
        "Доцент департамента права цифровых технологий и биоправа НИУ ВШЭ, кандидат юридических наук"
    ),
    "Бондарева Евгения Андреевна": (
        "Доцент департамента публичного права НИУ ВШЭ. Директор Группы по разрешению налоговых споров "
        "ООО «Деловые решения и технологии»"
    ),
    "Калимуллина Мадина Эмировна": (
        "Доцент факультета права НИУ ВШЭ, старший научный сотрудник Института права и развития ВШЭ — Сколково"
    ),
    "Синельникова Валентина Николаевна": (
        "Профессор-исследователь департамента частного права НИУ ВШЭ, доктор юридических наук"
    ),
}


@dataclass(frozen=True)
class Taught:
    title: str
    path: str


@dataclass
class Person:
    name: str
    tokens: frozenset[str]
    about: str
    programs: list[Taught] = field(default_factory=list)
    teacher: Teacher | None = None
    page: str = ""
    hidden: bool = False


def fix_text(text: str) -> str:
    for wrong, right in TEXT_FIXES:
        text = text.replace(wrong, right)
    return text


def name_tokens(name: str) -> frozenset[str]:
    cleaned = "".join(char if char.isalpha() or char.isspace() or char == "-" else " " for char in name.lower())
    return frozenset(word for word in cleaned.split() if len(word) >= MIN_TOKEN_LENGTH)


def same_person(person: Person, tokens: frozenset[str]) -> bool:
    return tokens <= person.tokens or person.tokens <= tokens


def has_photo(teacher: Teacher | None) -> bool:
    return bool(teacher and teacher.photo and teacher.photo.storage.exists(teacher.photo.name))


def absorb(person: Person, name: str, tokens: frozenset[str], about: str, taught: Taught, teacher: Teacher) -> None:
    if len(tokens) > len(person.tokens):
        person.name, person.tokens = name, tokens
    if about and len(about) > len(person.about):
        person.about = about
    if all(item.path != taught.path for item in person.programs):
        person.programs.append(taught)
    if not has_photo(person.teacher) and has_photo(teacher):
        person.teacher = teacher
    page = teacher_page(teacher)
    if not person.page and page:
        person.page = page
    person.hidden = person.hidden or not teacher.show_on_landing


def teacher_page(teacher: Teacher) -> str:
    url = teacher.page_url.strip()
    return url if url and is_hse_url(url) else ""


def merge(programs: list[Program]) -> list[Person]:
    people: list[Person] = []
    for program in programs:
        taught = Taught(title=program.title, path=f"/{program.path}")
        for link in program.program_teachers.all():
            name = link.teacher.name
            tokens = name_tokens(name)
            about = fix_text(link.about) if link.about else ""
            person = next((item for item in people if same_person(item, tokens)), None)
            if person is None:
                people.append(
                    Person(
                        name,
                        tokens,
                        about,
                        [taught],
                        link.teacher if has_photo(link.teacher) else None,
                        teacher_page(link.teacher),
                        not link.teacher.show_on_landing,
                    )
                )
            else:
                absorb(person, name, tokens, about, taught, link.teacher)
    return sorted(people, key=lambda person: (-len(person.programs), sort_key(person.name)))


def initials(name: str) -> str:
    words = name.split()
    if len(words) >= 3:
        return (words[1][0] + words[0][0]).upper()
    if len(words) == 2:
        return (words[0][0] + words[1][0]).upper()
    return words[0][0].upper() if words else ""


def about_text(person: Person) -> str:
    text = (TEACHER_ABOUT.get(person.name) or person.about).strip()
    return "" if TODO_MARK.search(text) else text


def photo_alt(name: str, about: str) -> str:
    post = about.split(",")[0].strip() if about else ""
    full = f"{name}, {post[0].lower()}{post[1:]}" if post else name
    return full if len(full) <= MAX_ALT_LENGTH else name


def photo(person: Person, about: str) -> TeacherPhotoOut | None:
    found: Photo | None = photo_with_webp(person.teacher.photo) if person.teacher else None
    if found is None:
        return None
    return TeacherPhotoOut(src=found.src, webp=found.webp, alt=photo_alt(person.name, about))


def payload(person: Person, about: str) -> str:
    data = {
        "name": person.name,
        "about": about,
        "programs": [{"t": item.title, "h": item.path} for item in person.programs],
        "url": person.page,
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def card(person: Person) -> TeacherCardOut:
    about = about_text(person)
    return TeacherCardOut(
        payload=payload(person, about),
        initials=initials(person.name),
        photo=photo(person, about),
        name=person.name,
        page=person.page,
        more_label=f"Подробнее: {person.name}",
        count=plural_programs(len(person.programs)),
        about=about,
    )


def teachers(programs: list[Program]) -> list[TeacherCardOut]:
    return [card(person) for person in merge(programs) if not person.hidden]
