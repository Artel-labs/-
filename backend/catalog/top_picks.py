from typing import Any

INITIAL_TOP = ("837181759", "816497962", "474596729", "1008772871", "474599435")


def pin_initial_top(programs: Any) -> None:
    for place, hse_id in enumerate(INITIAL_TOP, start=1):
        programs.filter(hse_id=hse_id).update(top_position=place)
