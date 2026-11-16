from datetime import datetime, timedelta

from app.services.attempts import deadline, is_expired, parse_selected, seconds_left

START = datetime(2026, 1, 1, 12, 0, 0)


def test_no_limit_means_no_deadline():
    assert deadline(START, 0) is None
    assert seconds_left(START, 0, START) is None
    assert not is_expired(START, 0, START + timedelta(days=5))


def test_seconds_left_counts_down():
    assert seconds_left(START, 10, START) == 600
    assert seconds_left(START, 10, START + timedelta(minutes=4)) == 360


def test_seconds_left_never_negative():
    assert seconds_left(START, 10, START + timedelta(hours=1)) == 0


def test_not_expired_within_time():
    assert not is_expired(START, 10, START + timedelta(minutes=9))


def test_not_expired_within_grace_period():
    assert not is_expired(START, 10, START + timedelta(minutes=10, seconds=20))


def test_expired_after_grace_period():
    assert is_expired(START, 10, START + timedelta(minutes=10, seconds=31))


def test_parse_selected_ignores_junk_and_foreign_ids():
    assert parse_selected(["1", "abc", "", "99", "3"], {1, 2, 3}) == [1, 3]


def test_parse_selected_removes_duplicates():
    assert parse_selected(["2", "2", "1"], {1, 2}) == [1, 2]


def test_parse_selected_empty():
    assert parse_selected([], {1, 2}) == []
