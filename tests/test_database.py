"""Tests for SQLite weather persistence."""

from datetime import UTC, datetime, timedelta

from app.database import get_latest_report, get_weather_history, save_report, utc_text
from app.models import WeatherReport


def make_report(temperature_f: float = 70.0) -> WeatherReport:
    return WeatherReport(
        observed_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
        collected_at=datetime(2026, 8, 31, 16, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=temperature_f,
    )


def test_save_and_read_latest_report(tmp_path) -> None:
    database_path = tmp_path / "weather.db"
    stored = save_report(make_report(), database_path)
    latest = get_latest_report("11234", database_path)
    assert stored.id == 1
    assert latest is not None
    assert latest.temperature_f == 70.0


def test_same_hour_updates_instead_of_duplicating(tmp_path) -> None:
    database_path = tmp_path / "weather.db"
    first = save_report(make_report(70.0), database_path)
    second = save_report(make_report(72.0), database_path)
    latest = get_latest_report("11234", database_path)
    assert second.id == first.id
    assert latest is not None
    assert latest.temperature_f == 72.0


def test_history_filters_and_paginates_newest_first(tmp_path) -> None:
    database_path = tmp_path / "weather.db"
    for hour in (16, 17, 18):
        report = make_report(float(hour))
        report.observed_at = datetime(2026, 8, 31, hour, tzinfo=UTC)
        save_report(report, database_path)

    reports, total = get_weather_history(
        "11234",
        datetime(2026, 8, 31, 16, tzinfo=UTC),
        datetime(2026, 9, 1, tzinfo=UTC),
        page=1,
        page_size=2,
        database_path=database_path,
    )

    assert total == 3
    assert [report.temperature_f for report in reports] == [18.0, 17.0]


def test_utc_text_uses_canonical_z_suffix() -> None:
    value = datetime(2026, 8, 31, 16, tzinfo=UTC)
    assert utc_text(value) == "2026-08-31T16:00:00Z"


def test_history_second_page_with_realistic_record_count(tmp_path) -> None:
    database_path = tmp_path / "weather.db"
    for hour_offset in range(30):
        report = make_report(float(hour_offset))
        report.observed_at = datetime(2026, 8, 1, tzinfo=UTC) + timedelta(
            hours=hour_offset
        )
        save_report(report, database_path)

    reports, total = get_weather_history(
        "11234",
        datetime(2026, 8, 1, tzinfo=UTC),
        datetime(2026, 8, 3, tzinfo=UTC),
        page=2,
        page_size=25,
        database_path=database_path,
    )

    assert total == 30
    assert len(reports) == 5
    assert [report.temperature_f for report in reports] == [4.0, 3.0, 2.0, 1.0, 0.0]
