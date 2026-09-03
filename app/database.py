"""Small SQLite persistence layer for hourly weather reports."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.config import DATABASE_PATH
from app.models import StoredWeatherReport, WeatherReport


COLUMNS = (
    "observed_at, collected_at, location_name, zip_code, temperature_f, "
    "apparent_temperature_f, relative_humidity_percent, dew_point_f, "
    "pressure_hpa, precipitation_inches, weather_code, cloud_cover_percent, "
    "visibility_miles, wind_speed_mph, wind_direction_degrees, wind_gusts_mph, "
    "uv_index, us_aqi, provider"
)


def utc_text(value: datetime) -> str:
    """Serialize UTC timestamps in one SQLite-sortable text format."""

    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def connect(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Open a database connection whose rows behave like dictionaries."""

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    """Create the weather table and index when they do not exist."""

    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observed_at TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                location_name TEXT NOT NULL,
                zip_code TEXT NOT NULL,
                temperature_f REAL,
                apparent_temperature_f REAL,
                relative_humidity_percent INTEGER,
                dew_point_f REAL,
                pressure_hpa REAL,
                precipitation_inches REAL,
                weather_code INTEGER,
                cloud_cover_percent INTEGER,
                visibility_miles REAL,
                wind_speed_mph REAL,
                wind_direction_degrees INTEGER,
                wind_gusts_mph REAL,
                uv_index REAL,
                us_aqi INTEGER,
                provider TEXT NOT NULL,
                UNIQUE(zip_code, observed_at)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_weather_zip_observed
            ON weather_reports(zip_code, observed_at DESC)
            """
        )


def save_report(
    report: WeatherReport, database_path: Path = DATABASE_PATH
) -> StoredWeatherReport:
    """Insert or update the snapshot for a ZIP code and observed hour."""

    initialize_database(database_path)
    values = report.model_dump(mode="json")
    column_names = COLUMNS.split(", ")
    placeholders = ", ".join(f":{name}" for name in column_names)
    updates = ", ".join(
        f"{name} = excluded.{name}"
        for name in column_names
        if name not in {"observed_at", "zip_code"}
    )
    with connect(database_path) as connection:
        connection.execute(
            f"""
            INSERT INTO weather_reports ({COLUMNS})
            VALUES ({placeholders})
            ON CONFLICT(zip_code, observed_at) DO UPDATE SET {updates}
            """,
            values,
        )
        row = connection.execute(
            """
            SELECT * FROM weather_reports
            WHERE zip_code = ? AND observed_at = ?
            """,
            (report.zip_code, values["observed_at"]),
        ).fetchone()
    if row is None:
        raise RuntimeError("Weather report could not be saved")
    return StoredWeatherReport.model_validate(dict(row))


def get_latest_report(
    zip_code: str, database_path: Path = DATABASE_PATH
) -> StoredWeatherReport | None:
    """Return the newest stored report for a ZIP code."""

    initialize_database(database_path)
    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM weather_reports
            WHERE zip_code = ?
            ORDER BY observed_at DESC
            LIMIT 1
            """,
            (zip_code,),
        ).fetchone()
    return StoredWeatherReport.model_validate(dict(row)) if row else None


def get_weather_history(
    zip_code: str,
    start_at: datetime,
    end_before: datetime,
    page: int,
    page_size: int,
    database_path: Path = DATABASE_PATH,
) -> tuple[list[StoredWeatherReport], int]:
    """Return a newest-first page within a half-open UTC time range."""

    initialize_database(database_path)
    start_value = utc_text(start_at)
    end_value = utc_text(end_before)
    offset = (page - 1) * page_size
    filters = "zip_code = ? AND observed_at >= ? AND observed_at < ?"
    parameters = (zip_code, start_value, end_value)
    with connect(database_path) as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM weather_reports WHERE {filters}", parameters
        ).fetchone()[0]
        rows = connection.execute(
            f"""
            SELECT * FROM weather_reports
            WHERE {filters}
            ORDER BY observed_at DESC
            LIMIT ? OFFSET ?
            """,
            (*parameters, page_size, offset),
        ).fetchall()
    reports = [StoredWeatherReport.model_validate(dict(row)) for row in rows]
    return reports, total
