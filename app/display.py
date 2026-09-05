"""Small presentation helpers used by the website."""

from datetime import UTC, datetime
from math import ceil
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


def aqi_status(value: int | None) -> tuple[str, str]:
    """Return the U.S. AQI label and matching CSS color name."""

    if value is None:
        return "Unavailable", "neutral"
    if value <= 50:
        return "Good", "good"
    if value <= 100:
        return "Moderate", "moderate"
    if value <= 150:
        return "Sensitive groups", "sensitive"
    if value <= 200:
        return "Unhealthy", "unhealthy"
    if value <= 300:
        return "Very unhealthy", "very-unhealthy"
    return "Hazardous", "hazardous"


def uv_status(value: float | None) -> tuple[str, str]:
    """Return the UV exposure label and matching CSS color name."""

    if value is None:
        return "Unavailable", "neutral"
    if value < 3:
        return "Low", "good"
    if value < 6:
        return "Moderate", "moderate"
    if value < 8:
        return "High", "sensitive"
    if value < 11:
        return "Very high", "unhealthy"
    return "Extreme", "hazardous"


def temperature_chart(
    reports: list[StoredWeatherReport], width: int = 700, height: int = 190
) -> dict[str, object] | None:
    """Build simple SVG coordinates for an oldest-to-newest temperature chart."""

    values = [report for report in reversed(reports) if report.temperature_f is not None]
    if not values:
        return None
    temperatures = [float(report.temperature_f) for report in values]
    minimum = min(temperatures)
    maximum = max(temperatures)
    temperature_range = maximum - minimum or 1
    horizontal_padding = 34
    vertical_padding = 30
    chart_width = width - (horizontal_padding * 2)
    chart_height = height - (vertical_padding * 2)
    divisor = max(1, len(values) - 1)
    label_interval = max(1, ceil(divisor / 6))
    points = []
    for index, (report, temperature) in enumerate(zip(values, temperatures)):
        x = horizontal_padding + (index / divisor) * chart_width
        y = vertical_padding + ((maximum - temperature) / temperature_range) * chart_height
        points.append(
            {
                "x": round(x, 1),
                "y": round(y, 1),
                "temperature": temperature,
                "time": eastern_time(report.observed_at).strftime("%I %p"),
                "show_time": index % label_interval == 0 or index == len(values) - 1,
            }
        )
    return {
        "points": points,
        "line": " ".join(f"{point['x']},{point['y']}" for point in points),
        "minimum": minimum,
        "maximum": maximum,
    }


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
