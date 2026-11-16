from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Attempt, AttemptAnswer, Test
from app.services.attempts import is_expired, parse_selected, seconds_left
from app.services.scoring import calculate_score, can_start_attempt

bp = Blueprint("student", __name__)


def _get_own_attempt(attempt_id):
    attempt = db.get_or_404(Attempt, attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)
    return attempt


def _summary(attempt):
    """Підсумок спроби: бали, відсоток і розбір кожного питання."""
    chosen = {}
    for answer in attempt.answers:
        chosen.setdefault(answer.question_id, set()).add(answer.option_id)

    questions_data = [
        {"id": q.id, "points": q.points, "correct": [o.id for o in q.options if o.is_correct]}
        for q in attempt.test.questions
    ]
    earned, maximum, percent = calculate_score(
        questions_data, {qid: list(ids) for qid, ids in chosen.items()}
    )

    rows = []
    for q in attempt.test.questions:
        selected = chosen.get(q.id, set())
        correct_ids = {o.id for o in q.options if o.is_correct}
        rows.append({"question": q, "selected": selected, "ok": selected == correct_ids})
    return earned, maximum, percent, rows


def _finish(attempt, form=None):
    """Зберігає відповіді, рахує результат. Повертає True, якщо час уже вийшов."""
    test = attempt.test
    now = datetime.utcnow()
    expired = is_expired(attempt.started_at, test.time_limit_min, now)

    if form is not None and not expired:
        for question in test.questions:
            valid_ids = {o.id for o in question.options}
            for option_id in parse_selected(form.getlist(f"q_{question.id}"), valid_ids):
                attempt.answers.append(AttemptAnswer(question_id=question.id, option_id=option_id))

    attempt.finished_at = now
    db.session.commit()

    attempt.score = _summary(attempt)[2]
    db.session.commit()
    return expired


def _user_attempts(test_id):
    return (
        Attempt.query.filter_by(test_id=test_id, user_id=current_user.id)
        .order_by(Attempt.id.desc())
        .all()
    )


@bp.route("/tests")
@login_required
def tests():
    available = [t for t in Test.query.order_by(Test.id.desc()).all() if t.questions]
    used = {}
    for attempt in Attempt.query.filter_by(user_id=current_user.id).all():
        used[attempt.test_id] = used.get(attempt.test_id, 0) + 1
    return render_template("student/tests.html", tests=available, used=used)


@bp.route("/tests/<int:test_id>")
@login_required
def test_info(test_id):
    test = db.get_or_404(Test, test_id)
    attempts = _user_attempts(test.id)
    unfinished = next((a for a in attempts if a.finished_at is None), None)
    can_start = bool(test.questions) and can_start_attempt(len(attempts), test.max_attempts)
    return render_template(
        "student/test_info.html",
        test=test,
        attempts=attempts,
        unfinished=unfinished,
        can_start=can_start,
    )


@bp.route("/tests/<int:test_id>/start", methods=["POST"])
@login_required
def start(test_id):
    test = db.get_or_404(Test, test_id)
    if not test.questions:
        flash("У цьому тесті ще немає питань", "warning")
        return redirect(url_for("student.test_info", test_id=test.id))

    attempts = _user_attempts(test.id)
    unfinished = next((a for a in attempts if a.finished_at is None), None)
    if unfinished:
        return redirect(url_for("student.take", attempt_id=unfinished.id))

    if not can_start_attempt(len(attempts), test.max_attempts):
        flash("Ліміт спроб для цього тесту вичерпано", "warning")
        return redirect(url_for("student.test_info", test_id=test.id))

    attempt = Attempt(test_id=test.id, user_id=current_user.id, started_at=datetime.utcnow())
    db.session.add(attempt)
    db.session.commit()
    return redirect(url_for("student.take", attempt_id=attempt.id))


@bp.route("/attempts/<int:attempt_id>")
@login_required
def take(attempt_id):
    attempt = _get_own_attempt(attempt_id)
    if attempt.finished_at is not None:
        return redirect(url_for("student.result", attempt_id=attempt.id))

    test = attempt.test
    now = datetime.utcnow()
    if is_expired(attempt.started_at, test.time_limit_min, now):
        _finish(attempt)
        flash("Час на виконання тесту вийшов", "warning")
        return redirect(url_for("student.result", attempt_id=attempt.id))

    return render_template(
        "student/take.html",
        attempt=attempt,
        test=test,
        seconds_left=seconds_left(attempt.started_at, test.time_limit_min, now),
    )


@bp.route("/attempts/<int:attempt_id>/submit", methods=["POST"])
@login_required
def submit(attempt_id):
    attempt = _get_own_attempt(attempt_id)
    if attempt.finished_at is None:
        if _finish(attempt, request.form):
            flash("Час вийшов, відповіді не враховано", "warning")
    return redirect(url_for("student.result", attempt_id=attempt.id))


@bp.route("/attempts/<int:attempt_id>/result")
@login_required
def result(attempt_id):
    attempt = _get_own_attempt(attempt_id)
    if attempt.finished_at is None:
        return redirect(url_for("student.take", attempt_id=attempt.id))
    earned, maximum, percent, rows = _summary(attempt)
    return render_template(
        "student/result.html",
        attempt=attempt,
        test=attempt.test,
        earned=earned,
        maximum=maximum,
        percent=percent,
        rows=rows,
    )


@bp.route("/attempts")
@login_required
def history():
    attempts = Attempt.query.filter_by(user_id=current_user.id).order_by(Attempt.id.desc()).all()
    return render_template("student/history.html", attempts=attempts)
