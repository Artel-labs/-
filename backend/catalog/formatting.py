NARROW_NO_BREAK_SPACE = "\u202f"
NO_BREAK_SPACE = "\u00a0"
RUBLE = "₽"


def format_price(amount: int) -> str:
    grouped = f"{amount:,}".replace(",", NARROW_NO_BREAK_SPACE)
    return f"{grouped}{NO_BREAK_SPACE}{RUBLE}"
