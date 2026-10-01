import pytest
from django.utils import translation
from django.utils.translation import gettext

ADMIN_PHRASES = {
    "Type to search": "Поиск",
    "No results found": "Ничего не найдено",
    "Filters": "Фильтры",
    "Return to site": "На сайт",
}


@pytest.mark.parametrize(("english", "russian"), ADMIN_PHRASES.items())
def test_admin_theme_speaks_russian(english, russian):
    with translation.override("ru"):
        assert gettext(english) == russian
