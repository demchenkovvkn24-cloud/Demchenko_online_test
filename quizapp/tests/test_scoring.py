from app.services.scoring import calculate_score, can_start_attempt, is_answer_correct

QUESTIONS = [
    {"id": 1, "points": 2, "correct": [10]},
    {"id": 2, "points": 3, "correct": [20, 21]},
]


def test_all_correct():
    assert calculate_score(QUESTIONS, {1: [10], 2: [20, 21]}) == (5, 5, 100.0)


def test_partial_multi_choice_is_wrong():
    assert calculate_score(QUESTIONS, {1: [10], 2: [20]}) == (2, 5, 40.0)


def test_unanswered_question():
    assert calculate_score(QUESTIONS, {}) == (0, 5, 0.0)


def test_no_questions():
    assert calculate_score([], {}) == (0, 0, 0.0)


def test_order_of_options_irrelevant():
    assert is_answer_correct([1, 2], [2, 1])


def test_attempt_limit():
    assert can_start_attempt(0, 1)
    assert not can_start_attempt(1, 1)
