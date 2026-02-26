import json
from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import Attempt, Content, User, db
from utils.chapter_config import (
    get_visible_contents_for_user,
    can_access_content,
)
from utils.score_calculator import calculate_score

user_bp = Blueprint("user", __name__)


# ---------------- INDEX ---------------- #

@user_bp.route("/")
def home():
    """Landing page with video background. No login required."""
    return render_template("home.html")


# ---------------- CHAPTERS (was INDEX) ---------------- #

@user_bp.route("/chapters")
def index():

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user.register"))

    from types import SimpleNamespace
    from models import HIDDEN_CHAPTERS, CHAPTER_REVEAL_TRIGGER

    real_contents, chapters_revealed = (
        get_visible_contents_for_user(user_id)
    )

    # Build a lookup: chapter_number -> real Content object
    real_by_num = {c.chapter_number: c for c in real_contents}

    # Slots 1-6: always displayed (real or placeholder)
    contents = []
    for num in range(1, 7):
        if num in real_by_num:
            contents.append(real_by_num[num])
        else:
            # Locked placeholder — no DB row yet
            contents.append(SimpleNamespace(
                id=None,
                chapter_number=num,
                title="Classified",
                accessible=False,
                is_placeholder=True,
                chapter_number_for_template=num,
            ))

    # Slots 7-8: only shown after chapter 6 is completed
    if chapters_revealed:
        for num in HIDDEN_CHAPTERS:
            if num in real_by_num:
                contents.append(real_by_num[num])
            else:
                contents.append(SimpleNamespace(
                    id=None,
                    chapter_number=num,
                    title="Classified",
                    accessible=False,
                    is_placeholder=True,
                ))

    # Only admins see the leaderboard
    if session.get("is_admin"):
        leaderboard_rows = (
            db.session.query(
                User.id,
                User.name,
                User.email,
                db.func.coalesce(
                    db.func.sum(Attempt.score), 0
                ).label("total_score"),
            )
            .outerjoin(Attempt)
            .group_by(User.id, User.name, User.email)
            .order_by(db.desc("total_score"))
            .limit(100)
            .all()
        )
        leaderboard = [
            {
                "user_id": r[0],
                "name": r[1],
                "email": r[2],
                "total_score": float(r[3] or 0),
            }
            for r in leaderboard_rows
        ]
    else:
        leaderboard = []

    return render_template(
        "index.html",
        contents=contents,
        leaderboard=leaderboard,
        chapters_revealed=chapters_revealed,
        is_admin=bool(session.get("is_admin")),
    )


# ---------------- LOGIN & LOGOUT ---------------- #

@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            return render_template("login.html", error="Email required.")

        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template(
                "login.html",
                error="Identity not found. Unauthorized.",
                email=email,
            )

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        return redirect(url_for("user.index"))

    return render_template("login.html")


@user_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.login"))


# ---------------- REGISTER ---------------- #

@user_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name or not email:
            return render_template(
                "register.html",
                error="Name and email required.",
                name=name,
                email=email,
            )

        user = User.query.filter_by(email=email).first()

        if user:
            return render_template(
                "register.html",
                error="Identity already registered. Proceed to Login.",
                name=name,
                email=email,
            )

        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        return redirect(url_for("user.index"))

    return render_template("register.html")


# ---------------- START ---------------- #

@user_bp.route("/start/<int:content_id>", methods=["POST"])
def start_challenge(content_id):

    if "user_id" not in session:
        return jsonify({"ok": False}), 401

    user_id = session["user_id"]

    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return jsonify({"ok": False, "error": "Locked"}), 403

    existing = Attempt.query.filter_by(
        user_id=user_id,
        content_id=content_id,
    ).first()

    if existing:
        return jsonify({"ok": False, "error": "Exists"}), 403

    attempt = Attempt(
        user_id=user_id,
        content_id=content_id,
        start_time=datetime.utcnow(),
    )

    db.session.add(attempt)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "attempt_id": attempt.id,
            "time_limit": content.time_limit,
        }
    )


# ---------------- CONTENT PAGE ---------------- #

@user_bp.route("/content/<int:content_id>")
def content_page(content_id):

    is_preview = request.args.get("preview") == "1"
    is_admin = session.get("is_admin")

    if is_preview and is_admin:
        # Admin Preview Bypass
        content = Content.query.get_or_404(content_id)
        attempted = False
    else:
        # Normal User Flow
        if "user_id" not in session:
            return redirect(url_for("user.register"))

        user_id = session["user_id"]
        content = Content.query.get_or_404(content_id)

        if not can_access_content(user_id, content_id):
            return "Locked", 403

        existing = Attempt.query.filter_by(
            user_id=user_id,
            content_id=content_id,
        ).first()

        attempted = existing is not None

    panels = []

    if content.panels_json:
        try:
            data = json.loads(content.panels_json)
            panels = data.get("panels", [])
        except Exception:
            panels = []

    # ── Video detection ──────────────────────────────────────────────────────
    # If the chapter has exactly one "panel" that is a video URL, switch to
    # video-player mode instead of the image carousel.
    VIDEO_EXTS   = (".mp4", ".webm", ".ogg", ".mov")
    VIDEO_HOSTS  = ("youtube.com/watch", "youtu.be/", "vimeo.com/", "cloudinary.com")

    is_video   = False
    video_url  = None
    video_type = None   # "youtube" | "vimeo" | "direct"

    if len(panels) == 1:
        raw = panels[0].strip()
        if any(raw.lower().endswith(ext) for ext in VIDEO_EXTS) or \
           any(vh in raw for vh in VIDEO_HOSTS):
            is_video = True
            # Convert YouTube watch → embed
            if "youtube.com/watch" in raw:
                import re as _re
                m = _re.search(r"[?&]v=([^&]+)", raw)
                vid = m.group(1) if m else ""
                video_url  = f"https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0"
                video_type = "youtube"
            elif "youtu.be/" in raw:
                vid = raw.split("youtu.be/")[-1].split("?")[0]
                video_url  = f"https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0"
                video_type = "youtube"
            elif "vimeo.com/" in raw:
                vid = raw.rstrip("/").split("/")[-1]
                video_url  = f"https://player.vimeo.com/video/{vid}?api=1"
                video_type = "vimeo"
            else:
                video_url  = raw
                video_type = "direct"

    return render_template(
        "content.html",
        content=content,
        attempted=attempted,
        panels=panels,
        is_preview=(is_preview and is_admin),
        is_video=is_video,
        video_url=video_url,
        video_type=video_type,
    )


# ---------------- PUZZLE ---------------- #

@user_bp.route("/puzzle/<int:content_id>")
def puzzle(content_id):
    """Red-thread matching puzzle — shown at the end of chapter 2."""
    if "user_id" not in session:
        return redirect(url_for("user.register"))

    user_id = session["user_id"]
    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return "Locked", 403

    # Ensure an Attempt row exists so /submit can finalise it
    existing = Attempt.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()
    if not existing:
        attempt = Attempt(
            user_id=user_id,
            content_id=content_id,
            start_time=datetime.utcnow(),
        )
        db.session.add(attempt)
        db.session.commit()

    return render_template("puzzle.html", content=content)


@user_bp.route("/callgame/<int:content_id>")
def callgame(content_id):
    """Call-history comparison game — shown at the end of chapter 5."""
    if "user_id" not in session:
        return redirect(url_for("user.register"))

    user_id = session["user_id"]
    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return "Locked", 403

    existing = Attempt.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()
    if not existing:
        attempt = Attempt(
            user_id=user_id,
            content_id=content_id,
            start_time=datetime.utcnow(),
        )
        db.session.add(attempt)
        db.session.commit()

    return render_template("callgame.html", content=content)


@user_bp.route("/codegate/<int:content_id>")
def codegate(content_id):
    """Zodiac-cipher code gate — shown at the end of chapter 7."""
    if "user_id" not in session:
        return redirect(url_for("user.register"))

    user_id = session["user_id"]
    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return "Locked", 403

    existing = Attempt.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()
    if not existing:
        attempt = Attempt(
            user_id=user_id,
            content_id=content_id,
            start_time=datetime.utcnow(),
        )
        db.session.add(attempt)
        db.session.commit()

    return render_template("codegate.html", content=content)


@user_bp.route("/quiz/<int:content_id>")
def quiz(content_id):
    """3-question interrogation quiz — shown at the end of chapter 4."""
    if "user_id" not in session:
        return redirect(url_for("user.register"))

    user_id = session["user_id"]
    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return "Locked", 403

    # Ensure an Attempt row exists so /submit can finalise it
    existing = Attempt.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()
    if not existing:
        attempt = Attempt(
            user_id=user_id,
            content_id=content_id,
            start_time=datetime.utcnow(),
        )
        db.session.add(attempt)
        db.session.commit()

    return render_template("quiz.html", content=content)


@user_bp.route("/api/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})

    return jsonify({
        "authenticated": True,
        "user": {
            "id": session["user_id"],
            "name": session.get("user_name"),
            "email": session.get("user_email"),
        },
    })

@user_bp.route("/submit/<int:content_id>", methods=["POST"])
def submit_result(content_id):

    if "user_id" not in session:
        return jsonify({"ok": False}), 401

    user_id = session["user_id"]

    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return jsonify({"ok": False, "error": "Locked"}), 403

    attempt = Attempt.query.filter_by(
        user_id=user_id,
        content_id=content_id,
    ).first()

    if not attempt:
        return jsonify({"ok": False}), 400

    if attempt.completed:
        return jsonify({"ok": False}), 400

    data = request.get_json() or {}
    completed = bool(data.get("completed"))

    end_time = datetime.utcnow()
    time_taken = int((end_time - attempt.start_time).total_seconds())

    attempt.end_time  = end_time
    attempt.time_taken = time_taken
    attempt.completed  = completed

    # ── Chapter points: +100 for completion ──────────────────────────────────
    chapter_points = 100 if completed else 0

    # ── Game completion bonus (only when completing the highest chapter) ──────
    bonus_points = 0
    if completed:
        # Determine the last chapter in the DB
        max_chapter = db.session.query(
            db.func.max(Content.chapter_number)
        ).scalar() or 0

        if content.chapter_number == max_chapter:
            # Count how many OTHER users have already completed this chapter
            prior_completions = (
                Attempt.query
                .filter(
                    Attempt.content_id == content_id,
                    Attempt.completed == True,     # noqa: E712
                    Attempt.user_id != user_id,
                )
                .count()
            )
            if prior_completions == 0:
                bonus_points = 500   # 1st to solve
            elif prior_completions == 1:
                bonus_points = 200   # 2nd to solve
            else:
                bonus_points = 100   # 3rd+

    attempt.score = chapter_points + bonus_points
    db.session.commit()

    revealed = (completed and content.chapter_number == 6)

    return jsonify({
        "ok": True,
        "chapter_points": chapter_points,
        "bonus_points":   bonus_points,
        "total_points":   chapter_points + bonus_points,
        "revealed":       revealed,
    })