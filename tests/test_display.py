"""Tests for human-readable website values."""

from datetime import UTC, datetime, timedelta

from app.display import time_ago


def test_time_ago_uses_friendly_units() -> None:
    now = datetime(2026, 9, 3, 12, tzinfo=UTC)

    assert time_ago(now - timedelta(seconds=20), now) == "just now"
    assert time_ago(now - timedelta(minutes=1), now) == "1 minute ago"
    assert time_ago(now - timedelta(hours=3), now) == "3 hours ago"
    assert time_ago(now - timedelta(days=2), now) == "2 days ago"
