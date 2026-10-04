import pytest

from catalog.typography import plain_spaces, squeeze_spaces, typeset

NB = " "
HAIR = " "


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Право – это искусство", f"Право{NB}— это искусство"),
        ("Реклама - вид деятельности", f"Реклама{NB}— вид деятельности"),
        ("Итог — диплом", f"Итог{NB}— диплом"),
        ("2021-2026", "2021–2026"),
        ("скидка 5-10%", f"скидка 5–10{NB}%"),
        ("19:00 - 22:10", "19:00–22:10"),
        ("с 10.00-18.00", f"с{NB}10.00–18.00"),
        ('курс "Право ЕС"', "курс «Право ЕС»"),
        ("университет «Высшая школа «экономики»»", "университет «Высшая школа „экономики“»"),
        ("© НИУ ВШЭ", f"©{NB}НИУ ВШЭ"),
        ("в работе и на практике", f"в{NB}работе и{NB}на{NB}практике"),
        ("25 лет и 30 000 ₽", f"25{NB}лет и{NB}30{NB}000{NB}₽"),
        ("спасибо Авакян Е.Г. за лекции", f"спасибо Авакян{NB}Е.{HAIR}Г. за{NB}лекции"),
        ("Е. Г. Авакян", f"Е.{HAIR}Г.{NB}Авакян"),
    ],
)
def test_rules(raw, expected):
    assert typeset(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "+7 (495) 772-95-90",
        "2026-09-21",
        "https://pravo.hse.ru/dpo-courses",
        "Расписание ИС263",
        "Корпоративное право",
    ],
)
def test_leaves_codes_and_addresses(raw):
    assert typeset(raw) == raw


def test_unbalanced_quotes_stay_as_is():
    assert typeset("«Национальный университет «Высшая школа»") == "«Национальный университет «Высшая школа»"


def test_lines_are_kept():
    assert typeset("в первой строке\nво второй") == f"в{NB}первой строке\nво{NB}второй"


def test_twice_is_same_as_once():
    text = 'Реклама - вид 5-10% "работы" в 2021-2026, Авакян Е.Г., © НИУ ВШЭ, 19:00 - 22:10'
    assert typeset(typeset(text)) == typeset(text)


def test_squeeze_keeps_special_spaces():
    assert squeeze_spaces(f"  в{NB}работе \n Е.{HAIR}Г.  ") == f"в{NB}работе Е.{HAIR}Г."


def test_plain_spaces_for_search():
    assert plain_spaces(f"в{NB}работе  Е.{HAIR}Г.") == "в работе Е. Г."
