"""Validated models used throughout the weather application."""

from datetime import datetime

from pydantic import BaseModel


class WeatherReport(BaseModel):
    """One hourly snapshot of weather and air-quality conditions."""

    observed_at: datetime
    collected_at: datetime
    location_name: str
    zip_code: str
    temperature_f: float | None = None
    apparent_temperature_f: float | None = None
    relative_humidity_percent: int | None = None
    dew_point_f: float | None = None
    pressure_hpa: float | None = None
    precipitation_inches: float | None = None
    weather_code: int | None = None
    cloud_cover_percent: int | None = None
    visibility_miles: float | None = None
    wind_speed_mph: float | None = None
    wind_direction_degrees: int | None = None
    wind_gusts_mph: float | None = None
    uv_index: float | None = None
    us_aqi: int | None = None
    provider: str = "Open-Meteo"


class StoredWeatherReport(WeatherReport):
    """A weather report returned after it has been stored."""

    id: int


class WeatherHistory(BaseModel):
    """One page of historical weather reports and pagination details."""

    reports: list[StoredWeatherReport]
    page: int
    page_size: int
    total: int
    total_pages: int
