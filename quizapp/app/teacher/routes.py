from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from app import db
from app.decorators import role_required
from app.forms import QuestionForm, TestForm
from app.models import AnswerOption, Question, Test
from app.services.questions import clean_options

bp = Blueprint("teacher", __name__, url_prefix="/teacher")

TEACHER_ROLES = ("teacher", "admin")


def _check_owner(test):
    """Редагувати тест може лише його автор або адміністратор."""
    if current_user.role != "admin" and test.author_id != current_user.id:
        abort(403)
    return test


def _get_own_test(test_id):
    return _check_owner(db.get_or_404(Test, test_id))


@bp.route("/tests")
@role_required(*TEACHER_ROLES)
def tests():
    query = Test.query
    if current_user.role != "admin":
        query = query.filter_by(author_id=current_user.id)
    return render_template("teacher/tests.html", tests=query.order_by(Test.id.desc()).all())


@bp.route("/tests/new", methods=["GET", "POST"])
@role_required(*TEACHER_ROLES)
def new_test():
    form = TestForm()
    if form.validate_on_submit():
        test = Test(
            title=form.title.data.strip(),
            description=(form.description.data or "").strip(),
            time_limit_min=form.time_limit_min.data,
            max_attempts=form.max_attempts.data,
            author_id=current_user.id,
        )
        db.session.add(test)
        db.session.commit()
        flash("Тест створено. Тепер додайте питання.", "success")
        return redirect(url_for("teacher.test_detail", test_id=test.id))
    return render_template("teacher/test_form.html", form=form, heading="Новий тест")


@bp.route("/tests/<int:test_id>")
@role_required(*TEACHER_ROLES)
def test_detail(test_id):
    test = _get_own_test(test_id)
    return render_template("teacher/test_detail.html", test=test)


@bp.route("/tests/<int:test_id>/edit", methods=["GET", "POST"])
@role_required(*TEACHER_ROLES)
def edit_test(test_id):
    test = _get_own_test(test_id)
    form = TestForm(obj=test)
    if form.validate_on_submit():
        test.title = form.title.data.strip()
        test.description = (form.description.data or "").strip()
        test.time_limit_min = form.time_limit_min.data
        test.max_attempts = form.max_attempts.data
        db.session.commit()
        flash("Зміни збережено", "success")
        return redirect(url_for("teacher.test_detail", test_id=test.id))
    return render_template("teacher/test_form.html", form=form, heading="Редагування тесту")


@bp.route("/tests/<int:test_id>/delete", methods=["POST"])
@role_required(*TEACHER_ROLES)
def delete_test(test_id):
    test = _get_own_test(test_id)
    db.session.delete(test)
    db.session.commit()
    flash("Тест видалено", "info")
    return redirect(url_for("teacher.tests"))


@bp.route("/tests/<int:test_id>/questions/new", methods=["GET", "POST"])
@role_required(*TEACHER_ROLES)
def new_question(test_id):
    test = _get_own_test(test_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(test_id=test.id, text=form.text.data.strip(), points=form.points.data)
        for text, is_correct in clean_options(form.raw_options()):
            question.options.append(AnswerOption(text=text, is_correct=is_correct))
        db.session.add(question)
        db.session.commit()
        flash("Питання додано", "success")
        return redirect(url_for("teacher.test_detail", test_id=test.id))
    return render_template("teacher/question_form.html", form=form, test=test)


@bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@role_required(*TEACHER_ROLES)
def delete_question(question_id):
    question = db.get_or_404(Question, question_id)
    test = _check_owner(question.test)
    db.session.delete(question)
    db.session.commit()
    flash("Питання видалено", "info")
    return redirect(url_for("teacher.test_detail", test_id=test.id))
