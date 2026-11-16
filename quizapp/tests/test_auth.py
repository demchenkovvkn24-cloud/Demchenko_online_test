from app import db
from app.models import User


def register(client, username="newuser", password="secret1", password2=None):
    return client.post(
        "/auth/register",
        data={"username": username, "password": password, "password2": password2 or password},
        follow_redirects=True,
    )


def login(client, username="student1", password="secret1"):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_register_creates_student(client, app):
    response = register(client)
    assert response.status_code == 200
    user = User.query.filter_by(username="newuser").first()
    assert user is not None
    assert user.role == "student"


def test_password_is_hashed(client, app):
    register(client)
    user = User.query.filter_by(username="newuser").first()
    assert user.password_hash != "secret1"
    assert user.check_password("secret1")


def test_register_duplicate_username(client, make_user):
    make_user("newuser")
    register(client, "newuser")
    assert User.query.filter_by(username="newuser").count() == 1


def test_register_short_password_rejected(client, app):
    register(client, password="123")
    assert User.query.filter_by(username="newuser").first() is None


def test_register_password_mismatch_rejected(client, app):
    register(client, password="secret1", password2="other")
    assert User.query.filter_by(username="newuser").first() is None


def test_login_success(client, make_user):
    make_user()
    response = login(client)
    assert response.status_code == 302


def test_login_wrong_password(client, make_user):
    make_user()
    response = login(client, password="wrong")
    assert response.status_code == 401


def test_logout_requires_post(client, make_user):
    make_user()
    login(client)
    assert client.get("/auth/logout").status_code == 405


def test_open_redirect_blocked(client, make_user):
    make_user()
    response = client.post(
        "/auth/login?next=https://evil.example", data={"username": "student1", "password": "secret1"}
    )
    assert response.status_code == 302
    assert "evil.example" not in response.headers["Location"]


def test_role_required_forbids_student(app, client, make_user):
    from app.decorators import role_required

    @app.route("/teacher-only")
    @role_required("teacher", "admin")
    def teacher_only():
        return "ok"

    make_user()
    login(client)
    assert client.get("/teacher-only").status_code == 403


def test_role_required_allows_teacher(app, client, make_user):
    from app.decorators import role_required

    @app.route("/teacher-only")
    @role_required("teacher", "admin")
    def teacher_only():
        return "ok"

    make_user("teacher1", role="teacher")
    login(client, "teacher1")
    assert client.get("/teacher-only").status_code == 200
