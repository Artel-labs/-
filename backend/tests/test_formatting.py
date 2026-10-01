from catalog.formatting import format_price


def test_price_does_not_break_between_digits_and_currency():
    assert format_price(150000) == "150\u202f000\u00a0₽"


def test_small_price_has_no_grouping():
    assert format_price(900) == "900\u00a0₽"
