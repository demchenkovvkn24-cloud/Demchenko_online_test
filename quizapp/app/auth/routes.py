from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app import db
from app.forms import LoginForm, RegisterForm
from app.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_safe_redirect(target):
    """Захист від open redirect: дозволені лише відносні адреси."""
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme and target.startswith("/")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegisterForm()
    if form.validate_on_submit():
        # Самореєстрація завжди створює студента; роль викладача видає адміністратор.
        user = User(username=form.username.data, role="student")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Реєстрація успішна. Тепер можна увійти.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Невірний логін або пароль", "danger")
            return render_template("auth/login.html", form=form), 401
        login_user(user)
        next_url = request.args.get("next")
        return redirect(next_url if _is_safe_redirect(next_url) else url_for("index"))
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Ви вийшли з акаунта", "info")
    return redirect(url_for("index"))
