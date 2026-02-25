"""
Chapter visibility and unlock logic.

Rules:
- Chapter 1: always accessible (no previous required)
- Chapters 2-6: each requires the previous chapter to be completed by the user
- Chapters 7-8 (HIDDEN): only visible/accessible after chapter 6 is completed
"""

from datetime import datetime
from typing import List, Optional, Tuple

from models import (
    Attempt,
    Content,
    CHAPTER_REVEAL_TRIGGER,
    HIDDEN_CHAPTERS,
)


def _content_with_chapter_number(chapter_num: int) -> Optional[Content]:
    return Content.query.filter_by(
        chapter_number=chapter_num
    ).first()


def _has_completed_chapter(user_id: int, chapter_num: int) -> bool:
    content = _content_with_chapter_number(chapter_num)
    if not content:
        return False

    attempt = Attempt.query.filter_by(
        user_id=user_id,
        content_id=content.id,
        completed=True
    ).first()

    return attempt is not None


def chapters_7_8_revealed_for_user(user_id: Optional[int]) -> bool:
    if not user_id:
        return False

    return _has_completed_chapter(
        user_id,
        CHAPTER_REVEAL_TRIGGER
    )


def _is_unlocked_by_time(content: Content) -> bool:
    if not content.is_unlocked:
        return False

    if content.unlock_time is None:
        return True

    return datetime.utcnow() >= content.unlock_time


def is_chapter_accessible_for_user(
    user_id: Optional[int],
    content: Content,
) -> bool:
    """
    Returns True if this specific user can enter/start this chapter.

    Sequential rule: chapters 2-6 require the previous chapter to be
    completed by this user. Chapter 1 is always open (if unlocked).
    Chapters 7-8 require chapter 6 completed.
    """
    if content.chapter_number in HIDDEN_CHAPTERS:
        if not user_id:
            return False
        return chapters_7_8_revealed_for_user(user_id)

    # Chapter must be marked as unlocked by admin first
    if not _is_unlocked_by_time(content):
        return False

    # Chapter 1 never requires a predecessor
    if content.chapter_number <= 1:
        return True

    # Chapters 2-6: user must have completed the previous chapter
    if not user_id:
        return False

    return _has_completed_chapter(user_id, content.chapter_number - 1)


def get_visible_contents_for_user(
    user_id: Optional[int]
) -> Tuple[List[Content], bool]:
    """
    Returns (list_of_visible_contents, chapters_7_8_revealed).

    Visible means the card is shown on the chapters page.
    Each card carries an `accessible` attribute so the template
    can distinguish locked vs unlocked state.
    """
    revealed = chapters_7_8_revealed_for_user(user_id)

    all_contents = Content.query.order_by(
        Content.chapter_number.asc()
    ).all()

    visible = []

    for c in all_contents:

        # Hidden chapters (7, 8): only show after chapter 6 complete
        if c.chapter_number in HIDDEN_CHAPTERS:
            if not revealed:
                continue
            # Attach accessibility flag
            c.accessible = True
            visible.append(c)
            continue

        # Regular chapters: show if admin has unlocked the chapter
        if _is_unlocked_by_time(c):
            c.accessible = is_chapter_accessible_for_user(user_id, c)
            visible.append(c)

    return visible, revealed


def can_access_content(
    user_id: Optional[int],
    content_id: int
) -> bool:
    """Gate used by /start and /content routes."""
    content = Content.query.get(content_id)

    if not content:
        return False

    return is_chapter_accessible_for_user(user_id, content)