from datetime import timezone

import click
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Увійдіть, щоб переглянути цю сторінку"
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401
    from app.auth.routes import bp as auth_bp
    from app.teacher.routes import bp as teacher_bp
    from app.student.routes import bp as student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    @app.template_filter("localtime")
    def localtime(value):
        """Час у БД зберігається в UTC; показуємо в часовому поясі комп'ютера."""
        if value is None:
            return "—"
        return value.replace(tzinfo=timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("403.html"), 403

    @app.cli.command("create-user")
    @click.argument("username")
    @click.argument("password")
    @click.option("--role", type=click.Choice(["student", "teacher", "admin"]), default="teacher")
    def create_user(username, password, role):
        """Створює користувача із заданою роллю (для викладачів та адмінів)."""
        user = models.User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Створено {role}: {username}")

    @app.cli.command("seed-demo")
    @click.option("--teacher", default="teacher1", show_default=True, help="Логін викладача-автора")
    def seed_demo(teacher):
        """Додає демонстраційний тест із питаннями вказаному викладачу."""
        from app.seed import create_demo_test

        author = models.User.query.filter_by(username=teacher).first()
        if author is None or author.role not in ("teacher", "admin"):
            raise click.ClickException(
                f"Викладача «{teacher}» не знайдено. Спершу виконайте create-user."
            )
        test = create_demo_test(author)
        if test is None:
            click.echo("Демонстраційний тест уже існує, нічого не додано.")
        else:
            click.echo(f"Створено тест «{test.title}»: {len(test.questions)} питань.")

    with app.app_context():
        db.create_all()

    return app
