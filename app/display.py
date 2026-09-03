"""Small presentation helpers used by the website."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.config import TIMEZONE
from app.models import StoredWeatherReport
from app.weather_codes import weather_label


EASTERN_ZONE = ZoneInfo(TIMEZONE)


def eastern_time(value: datetime) -> datetime:
    """Convert a stored UTC timestamp to New York local time."""

    return value.astimezone(EASTERN_ZONE)


def report_matches_search(report: StoredWeatherReport, query: str) -> bool:
    """Match plain search words against every value shown in history."""

    observed = eastern_time(report.observed_at)
    searchable = " ".join(
        str(value)
        for value in (
            observed.strftime("%Y-%m-%d %m/%d/%Y %b %B %d %Y %I:%M %p %Z"),
            report.location_name,
            report.zip_code,
            weather_label(report.weather_code),
            f"temperature temp {report.temperature_f} fahrenheit",
            f"humidity {report.relative_humidity_percent} percent",
            f"wind {report.wind_speed_mph} mph",
            f"uv {report.uv_index}",
            f"aqi air quality {report.us_aqi}",
            report.provider,
        )
    ).lower()
    return all(word in searchable for word in query.lower().split())


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
