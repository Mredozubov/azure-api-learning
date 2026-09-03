"""Small presentation helpers used by the website."""

from datetime import UTC, datetime


def time_ago(value: datetime, now: datetime | None = None) -> str:
    """Describe how long ago a timestamp occurred in simple words."""

    current = now or datetime.now(UTC)
    seconds = max(0, int((current - value.astimezone(UTC)).total_seconds()))
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"
