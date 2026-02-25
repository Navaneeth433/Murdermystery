def calculate_score(time_taken_seconds: int, time_limit_seconds: int, completed: bool) -> float:
    """
    Score is purely completion-based — no time factor.
    Completed → 100 points. Incomplete → 0 points.
    """
    return 100.0 if completed else 0.0



