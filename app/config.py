"""Application settings for the fixed Brooklyn weather station."""

import os
from pathlib import Path


LOCATION_NAME = os.getenv("WEATHER_LOCATION_NAME", "Brooklyn, NY 11234")
ZIP_CODE = os.getenv("WEATHER_ZIP_CODE", "11234")
LATITUDE = float(os.getenv("WEATHER_LATITUDE", "40.62"))
LONGITUDE = float(os.getenv("WEATHER_LONGITUDE", "-73.92"))
TIMEZONE = os.getenv("WEATHER_TIMEZONE", "America/New_York")
DATABASE_PATH = Path(os.getenv("WEATHER_DATABASE_PATH", "weather.db"))
STORAGE_BACKEND = os.getenv("WEATHER_STORAGE_BACKEND", "sqlite")
AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_TABLE_NAME = os.getenv("AZURE_TABLE_NAME", "weatherreports")
