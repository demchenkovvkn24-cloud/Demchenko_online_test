from app.models import AnswerOption, Question, Test
from app.seed import create_demo_test
from app.seed_data import DEMO_QUESTIONS
from app.services.questions import validate_options


def test_demo_data_is_valid():
    for text, points, options in DEMO_QUESTIONS:
        assert text and points >= 1
        assert validate_options(options) == [], text


def test_create_demo_test(app, make_user):
    teacher = make_user("t1", role="teacher")
    test = create_demo_test(teacher)
    assert test is not None
    assert Question.query.count() == len(DEMO_QUESTIONS)
    assert Test.query.one().author_id == teacher.id
    assert AnswerOption.query.filter_by(is_correct=True).count() >= len(DEMO_QUESTIONS)


def test_create_demo_test_is_idempotent(app, make_user):
    teacher = make_user("t1", role="teacher")
    create_demo_test(teacher)
    assert create_demo_test(teacher) is None
    assert Test.query.count() == 1


def test_seed_command(app, make_user):
    make_user("t1", role="teacher")
    result = app.test_cli_runner().invoke(args=["seed-demo", "--teacher", "t1"])
    assert result.exit_code == 0
    assert Question.query.count() == len(DEMO_QUESTIONS)


def test_seed_command_unknown_teacher(app):
    result = app.test_cli_runner().invoke(args=["seed-demo", "--teacher", "nobody"])
    assert result.exit_code != 0
    assert Test.query.count() == 0


def test_seed_command_rejects_student(app, make_user):
    make_user("s1", role="student")
    result = app.test_cli_runner().invoke(args=["seed-demo", "--teacher", "s1"])
    assert result.exit_code != 0
    assert Test.query.count() == 0
