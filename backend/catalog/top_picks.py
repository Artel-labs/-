from typing import Any

HIGH_RATING = ("494685723", "837181759", "894108285", "816497962", "1008772871", "1163275658", "474776084")


def pin_high_rating(programs: Any) -> None:
    programs.exclude(top_position=None).update(top_position=None)
    for place, hse_id in enumerate(HIGH_RATING, start=1):
        programs.filter(hse_id=hse_id).update(top_position=place)
