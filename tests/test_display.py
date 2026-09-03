"""Tests for human-readable website values."""

from datetime import UTC, datetime, timedelta

from app.display import eastern_time, time_ago


def test_time_ago_uses_friendly_units() -> None:
    now = datetime(2026, 9, 3, 12, tzinfo=UTC)

    assert time_ago(now - timedelta(seconds=20), now) == "just now"
    assert time_ago(now - timedelta(minutes=1), now) == "1 minute ago"
    assert time_ago(now - timedelta(hours=3), now) == "3 hours ago"
    assert time_ago(now - timedelta(days=2), now) == "2 days ago"


def test_eastern_time_uses_est_or_edt_for_the_date() -> None:
    winter = eastern_time(datetime(2026, 1, 15, 17, tzinfo=UTC))
    summer = eastern_time(datetime(2026, 7, 15, 16, tzinfo=UTC))

    assert winter.strftime("%I:%M %p %Z") == "12:00 PM EST"
    assert summer.strftime("%I:%M %p %Z") == "12:00 PM EDT"
