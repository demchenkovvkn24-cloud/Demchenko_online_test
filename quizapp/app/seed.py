from app import db
from app.models import AnswerOption, Question, Test
from app.seed_data import DEMO_DESCRIPTION, DEMO_QUESTIONS, DEMO_TITLE


def create_demo_test(author):
    """Створює демонстраційний тест для автора. Повертає тест або None, якщо він уже існує."""
    exists = Test.query.filter_by(author_id=author.id, title=DEMO_TITLE).first()
    if exists:
        return None

    test = Test(
        title=DEMO_TITLE,
        description=DEMO_DESCRIPTION,
        time_limit_min=10,
        max_attempts=3,
        author_id=author.id,
    )
    for text, points, options in DEMO_QUESTIONS:
        question = Question(text=text, points=points)
        for option_text, is_correct in options:
            question.options.append(AnswerOption(text=option_text, is_correct=is_correct))
        test.questions.append(question)

    db.session.add(test)
    db.session.commit()
    return test
