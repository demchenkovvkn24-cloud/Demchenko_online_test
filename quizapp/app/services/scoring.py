"""Бізнес-логіка оцінювання. Не залежить ні від Flask, ні від БД."""


def is_answer_correct(correct_ids, selected_ids):
    """Відповідь зарахована, лише якщо обрано рівно всі правильні варіанти."""
    return set(correct_ids) == set(selected_ids)


def calculate_score(questions, answers):
    """
    questions: список {"id", "points", "correct": [id, ...]}
    answers:   словник {question_id: [обрані id]}
    Повертає (набрано балів, максимум, відсоток).
    """
    earned = 0
    maximum = 0
    for q in questions:
        maximum += q["points"]
        if is_answer_correct(q["correct"], answers.get(q["id"], [])):
            earned += q["points"]
    percent = round(earned / maximum * 100, 1) if maximum else 0.0
    return earned, maximum, percent


def can_start_attempt(attempts_used, max_attempts):
    return attempts_used < max_attempts
