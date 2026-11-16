from app import db
from app.models import AnswerOption, Question, Test


def login(client, username, password="secret1"):
    return client.post("/auth/login", data={"username": username, "password": password})


def make_test(author_id, title="Тест 1"):
    test = Test(title=title, description="", time_limit_min=0, max_attempts=1, author_id=author_id)
    db.session.add(test)
    db.session.commit()
    return test.id


def valid_test_data(**overrides):
    data = {"title": "Основи Flask", "description": "Опис", "time_limit_min": "0", "max_attempts": "1"}
    data.update(overrides)
    return data


def valid_question_data(**overrides):
    data = {"text": "Столиця України?", "points": "2", "option_1": "Київ", "option_2": "Львів", "correct_1": "y"}
    data.update(overrides)
    return data


# ---------- доступ ----------

def test_student_cannot_open_dashboard(client, make_user):
    make_user()
    login(client, "student1")
    assert client.get("/teacher/tests").status_code == 403


def test_anonymous_redirected_to_login(client):
    response = client.get("/teacher/tests")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_teacher_sees_dashboard(client, make_user):
    make_user("t1", role="teacher")
    login(client, "t1")
    assert client.get("/teacher/tests").status_code == 200


# ---------- CRUD тесту ----------

def test_teacher_creates_test(client, make_user):
    teacher = make_user("t1", role="teacher")
    teacher_id = teacher.id
    login(client, "t1")
    response = client.post("/teacher/tests/new", data=valid_test_data())
    assert response.status_code == 302
    test = Test.query.one()
    assert test.title == "Основи Flask"
    assert test.author_id == teacher_id
    assert test.time_limit_min == 0


def test_zero_attempts_rejected(client, make_user):
    make_user("t1", role="teacher")
    login(client, "t1")
    client.post("/teacher/tests/new", data=valid_test_data(max_attempts="0"))
    assert Test.query.count() == 0


def test_empty_title_rejected(client, make_user):
    make_user("t1", role="teacher")
    login(client, "t1")
    client.post("/teacher/tests/new", data=valid_test_data(title=""))
    assert Test.query.count() == 0


def test_teacher_edits_own_test(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    client.post(f"/teacher/tests/{test_id}/edit", data=valid_test_data(title="Нова назва", max_attempts="3"))
    test = db.session.get(Test, test_id)
    assert test.title == "Нова назва"
    assert test.max_attempts == 3


def test_teacher_cannot_edit_foreign_test(client, make_user):
    owner = make_user("owner", role="teacher")
    test_id = make_test(owner.id, "Чужий тест")
    make_user("other", role="teacher")
    login(client, "other")
    response = client.post(f"/teacher/tests/{test_id}/edit", data=valid_test_data(title="Злам"))
    assert response.status_code == 403
    assert db.session.get(Test, test_id).title == "Чужий тест"


def test_teacher_cannot_delete_foreign_test(client, make_user):
    owner = make_user("owner", role="teacher")
    test_id = make_test(owner.id)
    make_user("other", role="teacher")
    login(client, "other")
    assert client.post(f"/teacher/tests/{test_id}/delete").status_code == 403
    assert Test.query.count() == 1


def test_admin_can_edit_any_test(client, make_user):
    owner = make_user("owner", role="teacher")
    test_id = make_test(owner.id)
    make_user("boss", role="admin")
    login(client, "boss")
    response = client.post(f"/teacher/tests/{test_id}/edit", data=valid_test_data(title="Від адміна"))
    assert response.status_code == 302
    assert db.session.get(Test, test_id).title == "Від адміна"


def test_delete_test_removes_questions_and_options(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    client.post(f"/teacher/tests/{test_id}/questions/new", data=valid_question_data())
    assert Question.query.count() == 1
    client.post(f"/teacher/tests/{test_id}/delete")
    assert Test.query.count() == 0
    assert Question.query.count() == 0
    assert AnswerOption.query.count() == 0


# ---------- питання ----------

def test_add_valid_question(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    response = client.post(f"/teacher/tests/{test_id}/questions/new", data=valid_question_data())
    assert response.status_code == 302
    question = Question.query.one()
    assert question.points == 2
    assert len(question.options) == 2
    correct = [o.text for o in question.options if o.is_correct]
    assert correct == ["Київ"]


def test_question_with_one_option_rejected(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    client.post(f"/teacher/tests/{test_id}/questions/new", data=valid_question_data(option_2=""))
    assert Question.query.count() == 0


def test_question_without_correct_rejected(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    data = valid_question_data()
    del data["correct_1"]
    client.post(f"/teacher/tests/{test_id}/questions/new", data=data)
    assert Question.query.count() == 0


def test_correct_flag_on_empty_option_rejected(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    client.post(f"/teacher/tests/{test_id}/questions/new", data=valid_question_data(correct_3="y"))
    assert Question.query.count() == 0


def test_cannot_add_question_to_foreign_test(client, make_user):
    owner = make_user("owner", role="teacher")
    test_id = make_test(owner.id)
    make_user("other", role="teacher")
    login(client, "other")
    response = client.post(f"/teacher/tests/{test_id}/questions/new", data=valid_question_data())
    assert response.status_code == 403
    assert Question.query.count() == 0


def test_delete_own_question(client, make_user):
    teacher = make_user("t1", role="teacher")
    test_id = make_test(teacher.id)
    login(client, "t1")
    client.post(f"/teacher/tests/{test_id}/questions/new", data=valid_question_data())
    question_id = Question.query.one().id
    client.post(f"/teacher/questions/{question_id}/delete")
    assert Question.query.count() == 0
    assert AnswerOption.query.count() == 0


def test_cannot_delete_foreign_question(client, make_user):
    owner = make_user("owner", role="teacher")
    test_id = make_test(owner.id)
    question = Question(test_id=test_id, text="?", points=1)
    question.options.append(AnswerOption(text="A", is_correct=True))
    db.session.add(question)
    db.session.commit()
    question_id = question.id
    make_user("other", role="teacher")
    login(client, "other")
    assert client.post(f"/teacher/questions/{question_id}/delete").status_code == 403
    assert Question.query.count() == 1
