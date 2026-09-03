"""Tests for conversion of Open-Meteo data into our weather model."""

from app.weather_client import OpenMeteoClient


def test_normalize_open_meteo_response() -> None:
    weather = {
        "current": {
            "time": "2026-08-31T12:45",
            "temperature_2m": 78.2,
            "relative_humidity_2m": 55,
            "apparent_temperature": 79.0,
            "dew_point_2m": 60.0,
            "pressure_msl": 1014.2,
            "precipitation": 0.01,
            "weather_code": 3,
            "cloud_cover": 80,
            "visibility": 16093.44,
            "wind_speed_10m": 8.5,
            "wind_direction_10m": 220,
            "wind_gusts_10m": 14.1,
        }
    }
    air = {"current": {"us_aqi": 42, "uv_index": 4.2}}
    report = OpenMeteoClient._normalize(weather, air)
    assert report.temperature_f == 78.2
    assert report.visibility_miles == 10.0
    assert report.us_aqi == 42
    assert report.uv_index == 4.2
    assert report.observed_at.isoformat() == "2026-08-31T16:00:00+00:00"
