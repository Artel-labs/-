import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")
NOTICE_MAX_AGE_DAYS = 90
NOTICE_DATE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
MONTHS_GENITIVE = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)  # fmt: skip
MONTHS_NOMINATIVE = (
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
)  # fmt: skip


def moscow_today() -> date:
    return datetime.now(MOSCOW).date()


def format_start(start: date | None, month_only: bool) -> str:
    if start is None:
        return ""
    if month_only:
        return f"{MONTHS_NOMINATIVE[start.month - 1]} {start.year} г."
    return f"{start.day} {MONTHS_GENITIVE[start.month - 1]} {start.year} г."


def parse_notice_date(raw: str) -> date | None:
    match = NOTICE_DATE.match(raw.strip())
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def notice_is_fresh(raw_date: str, today: date) -> bool:
    published = parse_notice_date(raw_date)
    return published is None or (today - published).days <= NOTICE_MAX_AGE_DAYS
