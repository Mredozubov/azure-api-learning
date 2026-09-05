"""Tests for human-readable website values."""

from datetime import UTC, datetime, timedelta

from app.display import aqi_status, eastern_time, temperature_chart, time_ago, uv_status
from app.models import StoredWeatherReport


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


def test_health_statuses_use_clear_labels() -> None:
    assert aqi_status(42) == ("Good", "good")
    assert aqi_status(58) == ("Moderate", "moderate")
    assert uv_status(0.0) == ("Low", "good")
    assert uv_status(4.2) == ("Moderate", "moderate")


def test_temperature_chart_orders_reports_oldest_first() -> None:
    newest = StoredWeatherReport(
        id=2,
        observed_at=datetime(2026, 9, 3, 5, tzinfo=UTC),
        collected_at=datetime(2026, 9, 3, 5, 1, tzinfo=UTC),
        location_name="Brooklyn",
        zip_code="11234",
        temperature_f=70,
    )
    oldest = newest.model_copy(
        update={"id": 1, "observed_at": datetime(2026, 9, 3, 4, tzinfo=UTC), "temperature_f": 68}
    )

    chart = temperature_chart([newest, oldest])

    assert chart is not None
    assert chart["minimum"] == 68
    assert chart["maximum"] == 70
    assert chart["points"][0]["temperature"] == 68


def test_temperature_chart_limits_time_labels_for_24_hours() -> None:
    newest = StoredWeatherReport(
        id=24,
        observed_at=datetime(2026, 9, 4, 4, tzinfo=UTC),
        collected_at=datetime(2026, 9, 4, 4, 1, tzinfo=UTC),
        location_name="Brooklyn",
        zip_code="11234",
        temperature_f=70,
    )
    reports = [
        newest.model_copy(
            update={
                "id": 24 - index,
                "observed_at": newest.observed_at - timedelta(hours=index),
                "temperature_f": 70 + index,
            }
        )
        for index in range(24)
    ]

    chart = temperature_chart(reports)

    assert chart is not None
    labeled_points = [point for point in chart["points"] if point["show_time"]]
    assert len(labeled_points) == 7
    assert chart["points"][0]["show_time"] is True
    assert chart["points"][-1]["show_time"] is True
