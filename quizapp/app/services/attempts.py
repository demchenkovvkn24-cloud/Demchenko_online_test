"""Бізнес-логіка проходження тесту: час і обробка відповідей. Не залежить від Flask і БД."""
from datetime import timedelta

GRACE_SECONDS = 30  # запас на затримку мережі при відправці після завершення часу


def deadline(started_at, time_limit_min):
    """Момент завершення спроби або None, якщо часу не обмежено."""
    if not time_limit_min:
        return None
    return started_at + timedelta(minutes=time_limit_min)


def seconds_left(started_at, time_limit_min, now):
    """Скільки секунд лишилось (не менше 0) або None, якщо часу не обмежено."""
    end = deadline(started_at, time_limit_min)
    if end is None:
        return None
    return max(0, int((end - now).total_seconds()))


def is_expired(started_at, time_limit_min, now, grace_seconds=GRACE_SECONDS):
    """Час вичерпано, навіть з урахуванням запасу."""
    end = deadline(started_at, time_limit_min)
    return end is not None and now > end + timedelta(seconds=grace_seconds)


def parse_selected(raw_values, valid_ids):
    """Перетворює значення форми на відсортований список id, лишаючи лише допустимі."""
    selected = set()
    for value in raw_values:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number in valid_ids:
            selected.add(number)
    return sorted(selected)
