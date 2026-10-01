NO_BREAK_SPACE = " "
RUBLE = "₽"


def format_price(amount: int) -> str:
    grouped = f"{amount:,}".replace(",", NO_BREAK_SPACE)
    return f"{grouped} {RUBLE}"


def unbreakable(text: str) -> str:
    return text.replace(" ", NO_BREAK_SPACE)
