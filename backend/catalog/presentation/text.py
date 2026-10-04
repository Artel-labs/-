from catalog.typography import squeeze_spaces


def plain_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def typographic_lines(text: str) -> list[str]:
    return [squeeze_spaces(line) for line in plain_lines(text)]


def plural(count: int, one: str, few: str, many: str) -> str:
    last, last_two = count % 10, count % 100
    if last == 1 and last_two != 11:
        return f"{count} {one}"
    if last in (2, 3, 4) and last_two not in (12, 13, 14):
        return f"{count} {few}"
    return f"{count} {many}"
