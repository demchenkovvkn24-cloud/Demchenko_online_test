from app.services.questions import clean_options, validate_options


def test_valid_options():
    assert validate_options([("A", False), ("B", True), ("", False), ("", False)]) == []


def test_clean_options_strips_and_drops_empty():
    assert clean_options([(" A ", True), ("", False), ("   ", False), ("B", False)]) == [("A", True), ("B", False)]


def test_too_few_options():
    errors = validate_options([("A", True), ("", False), ("", False), ("", False)])
    assert any("щонайменше 2" in e for e in errors)


def test_no_correct_option():
    errors = validate_options([("A", False), ("B", False)])
    assert any("правильну" in e for e in errors)


def test_correct_on_empty_option():
    errors = validate_options([("A", False), ("B", True), ("", True)])
    assert any("порожня" in e for e in errors)


def test_duplicate_options_case_insensitive():
    errors = validate_options([("Так", True), ("так", False)])
    assert any("повторюватися" in e for e in errors)


def test_multiple_correct_allowed():
    assert validate_options([("A", True), ("B", True), ("C", False)]) == []
