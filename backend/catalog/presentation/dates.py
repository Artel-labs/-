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


START_PREFIX = "Старт: "
EPOCH = date(1970, 1, 1)
MILLISECONDS = 1000


def is_upcoming(start: date | None, month_only: bool, today: date) -> bool:
    if start is None:
        return False
    if month_only:
        return (start.year, start.month) >= (today.year, today.month)
    return start >= today


def start_label(start: date | None, month_only: bool, today: date) -> str:
    if not is_upcoming(start, month_only, today):
        return ""
    return f"{START_PREFIX}{format_start(start, month_only)}"


def month_title(month: int) -> str:
    return MONTHS_NOMINATIVE[month - 1].capitalize()


def day_and_month(day: date) -> str:
    return f"{day.day} {MONTHS_GENITIVE[day.month - 1]}"


def epoch_day(day: date) -> int:
    return (day - EPOCH).days


def moscow_millis(day: date) -> int:
    return round(datetime.combine(day, datetime.min.time(), MOSCOW).timestamp() * MILLISECONDS)
