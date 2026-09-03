"""Open-Meteo client that converts provider JSON into our own model."""

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import LATITUDE, LOCATION_NAME, LONGITUDE, TIMEZONE, ZIP_CODE
from app.models import WeatherReport


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


class WeatherProviderError(RuntimeError):
    """Raised when the provider cannot supply a usable report."""


class OpenMeteoClient:
    """Retrieve current weather and air-quality data from Open-Meteo."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_current(self) -> WeatherReport:
        """Fetch and normalize the current snapshot for ZIP code 11234."""

        weather_params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "dew_point_2m,pressure_msl,precipitation,weather_code,"
                "cloud_cover,visibility,wind_speed_10m,wind_direction_10m,"
                "wind_gusts_10m"
            ),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": TIMEZONE,
            "forecast_days": 1,
        }
        air_params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "us_aqi,uv_index",
            "timezone": TIMEZONE,
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                weather_response = client.get(WEATHER_URL, params=weather_params)
                weather_response.raise_for_status()
                air_response = client.get(AIR_QUALITY_URL, params=air_params)
                air_response.raise_for_status()
        except httpx.HTTPError as error:
            raise WeatherProviderError(f"Open-Meteo request failed: {error}") from error

        try:
            return self._normalize(weather_response.json(), air_response.json())
        except (KeyError, TypeError, ValueError) as error:
            raise WeatherProviderError("Open-Meteo returned unexpected data") from error

    @staticmethod
    def _normalize(weather: dict[str, Any], air: dict[str, Any]) -> WeatherReport:
        current = weather["current"]
        current_air = air.get("current", {})
        observed_at = datetime.fromisoformat(current["time"])
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=ZoneInfo(TIMEZONE))
        visibility_meters = current.get("visibility")
        return WeatherReport(
            observed_at=observed_at.astimezone(UTC).replace(
                minute=0, second=0, microsecond=0
            ),
            collected_at=datetime.now(UTC),
            location_name=LOCATION_NAME,
            zip_code=ZIP_CODE,
            temperature_f=current.get("temperature_2m"),
            apparent_temperature_f=current.get("apparent_temperature"),
            relative_humidity_percent=current.get("relative_humidity_2m"),
            dew_point_f=current.get("dew_point_2m"),
            pressure_hpa=current.get("pressure_msl"),
            precipitation_inches=current.get("precipitation"),
            weather_code=current.get("weather_code"),
            cloud_cover_percent=current.get("cloud_cover"),
            visibility_miles=(
                round(visibility_meters / 1609.344, 2)
                if visibility_meters is not None
                else None
            ),
            wind_speed_mph=current.get("wind_speed_10m"),
            wind_direction_degrees=current.get("wind_direction_10m"),
            wind_gusts_mph=current.get("wind_gusts_10m"),
            uv_index=current_air.get("uv_index"),
            us_aqi=current_air.get("us_aqi"),
        )
