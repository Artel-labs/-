from datetime import date

from catalog.landing_schemas import ReviewCardOut, StartStripOut
from catalog.models import Program, Review
from catalog.presentation.dates import MONTHS_GENITIVE, MONTHS_NOMINATIVE, format_start, is_upcoming
from catalog.presentation.landing.teachers import fix_text
from catalog.presentation.text import en_dash

MAX_STARTS = 30
REVIEWS_PER_PROGRAM = 3
MAX_REVIEWS = 18
MIN_REVIEW_LENGTH = 180
MAX_REVIEW_LENGTH = 380
IDEAL_REVIEW_LENGTH = 280


def start_strip_item(program: Program, start: date) -> StartStripOut:
    if program.start_month_only:
        big, small, is_month = MONTHS_NOMINATIVE[start.month - 1], str(start.year), True
    else:
        big, small, is_month = str(start.day), MONTHS_GENITIVE[start.month - 1], False
    title = en_dash(program.title)
    return StartStripOut(
        path=f"/{program.path}",
        label=f"{title} – старт {format_start(start, program.start_month_only)}",
        big=big,
        small=small,
        is_month=is_month,
        title=title,
    )


def starts(programs: list[Program], today: date) -> list[StartStripOut]:
    dated = [
        (program, program.start_date)
        for program in programs
        if program.start_date and is_upcoming(program.start_date, program.start_month_only, today)
    ]
    dated.sort(key=lambda item: item[1])
    return [start_strip_item(program, start) for program, start in dated[:MAX_STARTS]]


def fitting_reviews(program: Program) -> list[Review]:
    fit = [
        review
        for review in program.reviews.all()
        if review.text and review.author and MIN_REVIEW_LENGTH <= len(review.text) <= MAX_REVIEW_LENGTH
    ]
    fit.sort(key=lambda review: abs(len(review.text) - IDEAL_REVIEW_LENGTH))
    return fit[:REVIEWS_PER_PROGRAM]


def review_card(program: Program, review: Review) -> ReviewCardOut:
    return ReviewCardOut(
        text=en_dash(fix_text(review.text).strip()),
        author=en_dash(review.author),
        path=f"/{program.path}",
        program=en_dash(program.title),
    )


def reviews(programs: list[Program]) -> list[ReviewCardOut]:
    pools = [(program, fit) for program in programs if (fit := fitting_reviews(program))]
    picks: list[ReviewCardOut] = []
    for round_number in range(REVIEWS_PER_PROGRAM):
        for program, pool in pools:
            if len(picks) >= MAX_REVIEWS:
                return picks
            if round_number < len(pool):
                picks.append(review_card(program, pool[round_number]))
    return picks
