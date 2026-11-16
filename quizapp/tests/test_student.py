from datetime import datetime, timedelta

from app import db
from app.models import Attempt, AttemptAnswer, AnswerOption, Question, Test, User


def login(client, username, password="secret1"):
    return client.post("/auth/login", data={"username": username, "password": password})


def make_quiz(author_id, max_attempts=2, time_limit=0):
    """Тест із двома питаннями: Q1 (2 б., одна правильна), Q2 (3 б., дві правильні)."""
    test = Test(title="Quiz", description="", time_limit_min=time_limit, max_attempts=max_attempts, author_id=author_id)
    q1 = Question(text="Q1", points=2)
    q1.options = [AnswerOption(text="A", is_correct=True), AnswerOption(text="B", is_correct=False)]
    q2 = Question(text="Q2", points=3)
    q2.options = [
        AnswerOption(text="C", is_correct=True),
        AnswerOption(text="D", is_correct=True),
        AnswerOption(text="E", is_correct=False),
    ]
    test.questions = [q1, q2]
    db.session.add(test)
    db.session.commit()
    ids = {o.text: o.id for q in test.questions for o in q.options}
    return test.id, q1.id, q2.id, ids


def start(client, test_id):
    return client.post(f"/tests/{test_id}/start")


def answers(q1, q2, q1_opts=(), q2_opts=()):
    data = {}
    if q1_opts:
        data[f"q_{q1}"] = [str(i) for i in q1_opts]
    if q2_opts:
        data[f"q_{q2}"] = [str(i) for i in q2_opts]
    return data


def setup(client, make_user, **quiz_kwargs):
    teacher = make_user("t1", role="teacher")
    quiz = make_quiz(teacher.id, **quiz_kwargs)
    make_user("s1")
    login(client, "s1")
    return quiz


# ---------- доступ і списки ----------

def test_anonymous_redirected(client):
    response = client.get("/tests")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_tests_list_shows_quiz(client, make_user):
    setup(client, make_user)
    response = client.get("/tests")
    assert response.status_code == 200
    assert "Quiz" in response.get_data(as_text=True)


def test_test_without_questions_not_listed_and_cannot_start(client, make_user):
    teacher = make_user("t1", role="teacher")
    empty = Test(title="Порожній", description="", time_limit_min=0, max_attempts=1, author_id=teacher.id)
    db.session.add(empty)
    db.session.commit()
    empty_id = empty.id
    make_user("s1")
    login(client, "s1")
    assert "Порожній" not in client.get("/tests").get_data(as_text=True)
    start(client, empty_id)
    assert Attempt.query.count() == 0


# ---------- старт ----------

def test_start_creates_attempt_and_take_page_opens(client, make_user):
    test_id, *_ = setup(client, make_user)
    response = start(client, test_id)
    assert response.status_code == 302
    attempt = Attempt.query.one()
    assert attempt.finished_at is None
    assert client.get(f"/attempts/{attempt.id}").status_code == 200


def test_start_twice_resumes_unfinished_attempt(client, make_user):
    test_id, *_ = setup(client, make_user)
    start(client, test_id)
    start(client, test_id)
    assert Attempt.query.count() == 1


def test_attempt_limit_enforced(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user, max_attempts=1)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2))
    start(client, test_id)
    assert Attempt.query.count() == 1


# ---------- оцінювання ----------

def test_perfect_score(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(
        f"/attempts/{attempt_id}/submit",
        data=answers(q1, q2, [ids["A"]], [ids["C"], ids["D"]]),
    )
    attempt = db.session.get(Attempt, attempt_id)
    assert attempt.finished_at is not None
    assert attempt.score == 100.0
    assert AttemptAnswer.query.count() == 3


def test_partial_score(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2, [ids["A"]]))
    assert db.session.get(Attempt, attempt_id).score == 40.0


def test_incomplete_multi_choice_is_wrong(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2, [ids["A"]], [ids["C"]]))
    assert db.session.get(Attempt, attempt_id).score == 40.0


def test_empty_submission_scores_zero(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(f"/attempts/{attempt_id}/submit", data={})
    assert db.session.get(Attempt, attempt_id).score == 0.0


def test_foreign_option_id_is_ignored(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    # варіант питання 2 підставлено у відповідь на питання 1
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2, [ids["C"]]))
    assert db.session.get(Attempt, attempt_id).score == 0.0
    assert AttemptAnswer.query.count() == 0


def test_second_submit_does_not_change_result(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2, [ids["A"]], [ids["C"], ids["D"]]))
    client.post(f"/attempts/{attempt_id}/submit", data={})
    assert db.session.get(Attempt, attempt_id).score == 100.0


# ---------- час ----------

def test_late_submission_is_graded_empty(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user, time_limit=10)
    student_id = User.query.filter_by(username="s1").one().id
    attempt = Attempt(test_id=test_id, user_id=student_id, started_at=datetime.utcnow() - timedelta(hours=2))
    db.session.add(attempt)
    db.session.commit()
    attempt_id = attempt.id
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2, [ids["A"]], [ids["C"], ids["D"]]))
    assert db.session.get(Attempt, attempt_id).score == 0.0


def test_opening_expired_attempt_finalizes_it(client, make_user):
    test_id, *_ = setup(client, make_user, time_limit=10)
    student_id = User.query.filter_by(username="s1").one().id
    attempt = Attempt(test_id=test_id, user_id=student_id, started_at=datetime.utcnow() - timedelta(hours=2))
    db.session.add(attempt)
    db.session.commit()
    attempt_id = attempt.id
    response = client.get(f"/attempts/{attempt_id}")
    assert response.status_code == 302
    assert "/result" in response.headers["Location"]
    assert db.session.get(Attempt, attempt_id).finished_at is not None


# ---------- чужі спроби та сторінки результату ----------

def test_cannot_view_or_submit_foreign_attempt(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id, q1, q2, ids = make_quiz(teacher.id)
    owner = make_user("owner")
    attempt = Attempt(test_id=test_id, user_id=owner.id, started_at=datetime.utcnow())
    db.session.add(attempt)
    db.session.commit()
    attempt_id = attempt.id
    make_user("intruder")
    login(client, "intruder")
    assert client.get(f"/attempts/{attempt_id}").status_code == 403
    assert client.post(f"/attempts/{attempt_id}/submit", data={}).status_code == 403
    assert client.get(f"/attempts/{attempt_id}/result").status_code == 403


def test_result_of_unfinished_attempt_redirects_to_take(client, make_user):
    test_id, *_ = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    response = client.get(f"/attempts/{attempt_id}/result")
    assert response.status_code == 302
    assert f"/attempts/{attempt_id}" in response.headers["Location"]


def test_result_page_and_history(client, make_user):
    test_id, q1, q2, ids = setup(client, make_user)
    start(client, test_id)
    attempt_id = Attempt.query.one().id
    client.post(f"/attempts/{attempt_id}/submit", data=answers(q1, q2, [ids["A"]], [ids["C"], ids["D"]]))
    result = client.get(f"/attempts/{attempt_id}/result")
    assert result.status_code == 200
    assert "100.0" in result.get_data(as_text=True)
    history = client.get("/attempts")
    assert history.status_code == 200
    assert "Quiz" in history.get_data(as_text=True)
