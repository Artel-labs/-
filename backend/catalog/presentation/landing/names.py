from dataclasses import dataclass

LATIN_SEPARATOR = " / "
PATRONYMIC_ENDINGS = ("вич", "вна", "ична", "ьич")
GIVEN_FIRST_WORDS = 2
PATRONYMIC_LAST_WORDS = 3
RUSSIAN_GIVEN_NAMES = frozenset(
    [
        "Александр",
        "Александра",
        "Алексей",
        "Алёна",
        "Алена",
        "Алина",
        "Алиса",
        "Алла",
        "Анастасия",
        "Анатолий",
        "Андрей",
        "Анжелика",
        "Анна",
        "Антон",
        "Арина",
        "Аркадий",
        "Арсений",
        "Артём",
        "Артем",
        "Артур",
        "Богдан",
        "Борис",
        "Вадим",
        "Валентин",
        "Валентина",
        "Валерий",
        "Валерия",
        "Варвара",
        "Василий",
        "Василиса",
        "Вера",
        "Вероника",
        "Виктор",
        "Виктория",
        "Виолетта",
        "Виталий",
        "Владимир",
        "Владислав",
        "Владислава",
        "Всеволод",
        "Вячеслав",
        "Галина",
        "Геннадий",
        "Георгий",
        "Герман",
        "Глеб",
        "Григорий",
        "Дарья",
        "Денис",
        "Диана",
        "Дина",
        "Дмитрий",
        "Евгений",
        "Евгения",
        "Евдокия",
        "Егор",
        "Екатерина",
        "Елена",
        "Елизавета",
        "Жанна",
        "Зарина",
        "Захар",
        "Зоя",
        "Иван",
        "Игорь",
        "Илья",
        "Инна",
        "Ирина",
        "Карина",
        "Кира",
        "Кирилл",
        "Клавдия",
        "Константин",
        "Кристина",
        "Ксения",
        "Лариса",
        "Лев",
        "Леонид",
        "Лидия",
        "Лилия",
        "Любовь",
        "Людмила",
        "Мадина",
        "Майя",
        "Марат",
        "Маргарита",
        "Марина",
        "Мария",
        "Марк",
        "Матвей",
        "Милана",
        "Мирон",
        "Михаил",
        "Надежда",
        "Наталия",
        "Наталья",
        "Никита",
        "Николай",
        "Нина",
        "Оксана",
        "Олег",
        "Олеся",
        "Ольга",
        "Павел",
        "Полина",
        "Раиса",
        "Регина",
        "Роман",
        "Руслан",
        "Савелий",
        "Светлана",
        "Семён",
        "Семен",
        "Сергей",
        "Снежана",
        "София",
        "Софья",
        "Станислав",
        "Степан",
        "Тамара",
        "Тарас",
        "Татьяна",
        "Тимофей",
        "Тимур",
        "Ульяна",
        "Фёдор",
        "Федор",
        "Филипп",
        "Эвелина",
        "Эдуард",
        "Элина",
        "Эльвира",
        "Эмилия",
        "Юлиан",
        "Юлия",
        "Юрий",
        "Яна",
        "Ярослав",
        "Ярослава",
    ]
)


@dataclass(frozen=True)
class PersonName:
    surname: str
    given: str = ""
    patronymic: str = ""
    latin: str = ""

    @property
    def short(self) -> str:
        return " ".join(part for part in (self.surname, self.given) if part)

    @property
    def full(self) -> str:
        cyrillic = " ".join(part for part in (self.surname, self.given, self.patronymic) if part)
        return f"{cyrillic}{LATIN_SEPARATOR}{self.latin}" if self.latin else cyrillic

    @property
    def initials(self) -> str:
        return "".join(part[0] for part in (self.given, self.surname) if part).upper()


def is_patronymic(word: str) -> bool:
    return word.lower().endswith(PATRONYMIC_ENDINGS)


def three_words(first: str, second: str, third: str) -> PersonName:
    if first in RUSSIAN_GIVEN_NAMES and is_patronymic(second):
        return PersonName(third, first, second)
    if is_patronymic(third):
        return PersonName(first, second, third)
    if is_patronymic(second):
        return PersonName(third, first, second)
    return PersonName(first, f"{second} {third}")


def two_words(first: str, second: str) -> PersonName:
    if first in RUSSIAN_GIVEN_NAMES:
        return PersonName(second, first)
    return PersonName(first, second)


def cyrillic_part(words: list[str]) -> PersonName:
    if len(words) == PATRONYMIC_LAST_WORDS:
        return three_words(*words)
    if len(words) == GIVEN_FIRST_WORDS:
        return two_words(*words)
    return PersonName(" ".join(words))


def parse_name(raw: str) -> PersonName:
    cyrillic, _, latin = raw.partition(LATIN_SEPARATOR)
    parsed = cyrillic_part(cyrillic.split())
    return PersonName(parsed.surname, parsed.given, parsed.patronymic, latin.strip())
