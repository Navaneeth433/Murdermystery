def calculate_score(time_taken_seconds: int, time_limit_seconds: int, completed: bool) -> float:
    """
    Calculate score for a challenge attempt.

    Max score per content = 100

    completion_score = 70 (if completed)
    speed_score = 30 × (1 - time_taken / time_limit)
    total_score = completion_score + speed_score

    If not completed → score = 0
    If time_taken exceeds time_limit, speed_score bottoms at 0.
    """
    if not completed:
        return 0.0

    if time_limit_seconds <= 0:
        # Avoid division by zero; give only completion score.
        return 70.0

    completion_score = 70.0
    ratio = min(max(time_taken_seconds / time_limit_seconds, 0.0), 10.0)
    # Cap ratio at 1 for speed score; anything slower gets 0 in speed portion.
    speed_factor = max(0.0, 1.0 - min(ratio, 1.0))
    speed_score = 30.0 * speed_factor
    return completion_score + speed_score



