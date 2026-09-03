"""Tests for the FastAPI weather endpoints."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.models import StoredWeatherReport


client = TestClient(app)


def test_home_page_shows_empty_state(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_latest_report", lambda _zip_code: None)

    response = client.get("/")

    assert response.status_code == 200
    assert "Collect the first weather report" in response.text


def test_home_page_shows_current_weather(monkeypatch) -> None:
    report = StoredWeatherReport(
        id=1,
        observed_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
        collected_at=datetime(2026, 8, 31, 16, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=78.2,
        apparent_temperature_f=79.0,
        relative_humidity_percent=55,
        weather_code=2,
        wind_speed_mph=8.5,
        precipitation_inches=0,
        visibility_miles=10,
        uv_index=4.2,
        us_aqi=42,
    )
    monkeypatch.setattr("app.main.get_latest_report", lambda _zip_code: report)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Brooklyn, NY" in response.text
    assert "Partly cloudy" in response.text
    assert "78" in response.text
    assert "12:00 PM EDT" in response.text


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_docs_link_back_to_current_weather() -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert 'href="/">← Current weather</a>' in response.text


def test_latest_weather_returns_404_when_empty(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_latest_report", lambda _zip_code: None)
    response = client.get("/api/weather/latest")
    assert response.status_code == 404
    assert "Run python -m app.collector" in response.json()["detail"]


def test_latest_weather_returns_report(monkeypatch) -> None:
    report = StoredWeatherReport(
        id=1,
        observed_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
        collected_at=datetime(2026, 8, 31, 16, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=78.2,
        relative_humidity_percent=55,
    )
    monkeypatch.setattr("app.main.get_latest_report", lambda _zip_code: report)
    response = client.get("/api/weather/latest")
    assert response.status_code == 200
    assert response.json()["temperature_f"] == 78.2
    assert response.json()["zip_code"] == "11234"


def test_history_returns_paginated_reports(monkeypatch) -> None:
    report = StoredWeatherReport(
        id=1,
        observed_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
        collected_at=datetime(2026, 8, 31, 16, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=78.2,
    )
    monkeypatch.setattr(
        "app.main.get_weather_history",
        lambda *_args: ([report], 26),
    )

    response = client.get(
        "/api/weather/history?start=2026-08-01&end=2026-08-31&page=2&page_size=25"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 26
    assert response.json()["total_pages"] == 2
    assert response.json()["page"] == 2
    assert len(response.json()["reports"]) == 1


def test_history_rejects_reversed_dates() -> None:
    response = client.get(
        "/api/weather/history?start=2026-09-01&end=2026-08-31"
    )

    assert response.status_code == 400
    assert "end date" in response.json()["detail"]


def test_history_validates_page_size() -> None:
    response = client.get(
        "/api/weather/history?start=2026-08-01&end=2026-08-31&page_size=101"
    )

    assert response.status_code == 422


def test_history_page_renders_search_results(monkeypatch) -> None:
    report = StoredWeatherReport(
        id=1,
        observed_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
        collected_at=datetime(2026, 8, 31, 16, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=78.2,
        relative_humidity_percent=55,
        weather_code=3,
        wind_speed_mph=8.5,
        uv_index=4.2,
        us_aqi=42,
    )
    monkeypatch.setattr(
        "app.main.get_weather_history", lambda *_args: ([report], 1)
    )

    response = client.get("/history")

    assert response.status_code == 200
    assert "Weather history" in response.text
    assert "Overcast" in response.text
    assert "1</strong> observations found" in response.text
    assert "12:00 PM EDT" in response.text


def test_history_page_searches_all_displayed_categories(monkeypatch) -> None:
    matching = StoredWeatherReport(
        id=1,
        observed_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
        collected_at=datetime(2026, 8, 31, 16, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=78.2,
        relative_humidity_percent=55,
        weather_code=3,
        wind_speed_mph=8.5,
        uv_index=4.2,
        us_aqi=42,
    )
    not_matching = matching.model_copy(
        update={"id": 2, "weather_code": 0, "us_aqi": 18}
    )
    monkeypatch.setattr(
        "app.main.get_weather_history",
        lambda *_args: ([matching, not_matching], 2),
    )

    response = client.get("/history?q=overcast+aqi+42")

    assert response.status_code == 200
    assert "1</strong> observations matching" in response.text
    assert "Overcast" in response.text
    assert "Clear sky" not in response.text
