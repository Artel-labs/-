from catalog.formatting import format_price, unbreakable


def test_price_matches_previous_site():
    assert format_price(150000) == "150 000 ₽"


def test_small_price_has_no_grouping():
    assert format_price(900) == "900 ₽"


def test_unbreakable_keeps_price_on_one_line():
    assert unbreakable(format_price(150000)) == "150 000 ₽"
