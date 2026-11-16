"""Бізнес-логіка валідації питань. Не залежить ні від Flask, ні від БД."""

MIN_OPTIONS = 2


def clean_options(raw):
    """raw: список (текст, чи_правильна). Повертає лише непорожні варіанти з обрізаними пробілами."""
    return [(text.strip(), bool(correct)) for text, correct in raw if text and text.strip()]


def validate_options(raw):
    """Повертає список повідомлень про помилки (порожній список — усе гаразд)."""
    errors = []

    if any(correct and not (text and text.strip()) for text, correct in raw):
        errors.append("Правильною не може бути порожня відповідь")

    cleaned = clean_options(raw)

    if len(cleaned) < MIN_OPTIONS:
        errors.append(f"Потрібно щонайменше {MIN_OPTIONS} варіанти відповіді")

    texts = [text.lower() for text, _ in cleaned]
    if len(texts) != len(set(texts)):
        errors.append("Варіанти відповіді не повинні повторюватися")

    if not any(correct for _, correct in cleaned):
        errors.append("Позначте хоча б одну правильну відповідь")

    return errors
