from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from app.models import User
from app.services.questions import validate_options

OPTION_SLOTS = 4


class RegisterForm(FlaskForm):
    username = StringField(
        "Логін",
        validators=[
            DataRequired(message="Вкажіть логін"),
            Length(3, 32, message="Логін має містити від 3 до 32 символів"),
            Regexp(r"^[A-Za-z0-9_.-]+$", message="Дозволені лише латиниця, цифри та символи _ . -"),
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(message="Вкажіть пароль"), Length(min=6, message="Пароль має містити щонайменше 6 символів")],
    )
    password2 = PasswordField(
        "Повторіть пароль",
        validators=[DataRequired(), EqualTo("password", message="Паролі не збігаються")],
    )
    submit = SubmitField("Зареєструватися")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Такий логін уже зайнятий")


class LoginForm(FlaskForm):
    username = StringField("Логін", validators=[DataRequired(message="Вкажіть логін")])
    password = PasswordField("Пароль", validators=[DataRequired(message="Вкажіть пароль")])
    submit = SubmitField("Увійти")


class TestForm(FlaskForm):
    title = StringField(
        "Назва тесту",
        validators=[DataRequired(message="Вкажіть назву"), Length(max=200, message="Не більше 200 символів")],
    )
    description = TextAreaField("Опис", validators=[Optional(), Length(max=2000)])
    # InputRequired (а не DataRequired), бо 0 — допустиме значення («без обмеження»)
    time_limit_min = IntegerField(
        "Ліміт часу, хв (0 — без обмеження)",
        default=0,
        validators=[InputRequired(message="Вкажіть число"), NumberRange(0, 300, "Від 0 до 300 хвилин")],
    )
    max_attempts = IntegerField(
        "Кількість спроб",
        default=1,
        validators=[InputRequired(message="Вкажіть число"), NumberRange(1, 20, "Від 1 до 20 спроб")],
    )
    submit = SubmitField("Зберегти")


class QuestionForm(FlaskForm):
    text = TextAreaField(
        "Текст питання",
        validators=[DataRequired(message="Введіть текст питання"), Length(max=2000)],
    )
    points = IntegerField(
        "Бали за питання",
        default=1,
        validators=[InputRequired(message="Вкажіть число"), NumberRange(1, 100, "Від 1 до 100 балів")],
    )
    option_1 = StringField("Варіант 1", validators=[Optional(), Length(max=300)])
    option_2 = StringField("Варіант 2", validators=[Optional(), Length(max=300)])
    option_3 = StringField("Варіант 3", validators=[Optional(), Length(max=300)])
    option_4 = StringField("Варіант 4", validators=[Optional(), Length(max=300)])
    correct_1 = BooleanField("Правильна")
    correct_2 = BooleanField("Правильна")
    correct_3 = BooleanField("Правильна")
    correct_4 = BooleanField("Правильна")
    submit = SubmitField("Додати питання")

    options_errors = ()

    def raw_options(self):
        return [
            (getattr(self, f"option_{i}").data or "", getattr(self, f"correct_{i}").data)
            for i in range(1, OPTION_SLOTS + 1)
        ]

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        self.options_errors = validate_options(self.raw_options())
        return ok and not self.options_errors
