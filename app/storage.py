"""Choose local SQLite or production Azure Table Storage."""

from datetime import datetime
from pathlib import Path
from typing import Protocol

from app import config
from app.azure_table_store import AzureTableWeatherStore
from app.database import (
    get_latest_report as sqlite_latest,
    get_weather_history as sqlite_history,
    initialize_database,
    save_report as sqlite_save,
)
from app.models import StoredWeatherReport, WeatherReport


class WeatherStore(Protocol):
    """Operations that both storage systems must provide."""

    def initialize(self) -> None: ...
    def save(self, report: WeatherReport) -> StoredWeatherReport: ...
    def latest(self, zip_code: str) -> StoredWeatherReport | None: ...
    def history(
        self,
        zip_code: str,
        start_at: datetime,
        end_before: datetime,
        page: int,
        page_size: int,
    ) -> tuple[list[StoredWeatherReport], int]: ...


class SQLiteWeatherStore:
    """Use the existing SQLite functions behind the shared interface."""

    def __init__(self, database_path: Path = config.DATABASE_PATH) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        initialize_database(self.database_path)

    def save(self, report: WeatherReport) -> StoredWeatherReport:
        return sqlite_save(report, self.database_path)

    def latest(self, zip_code: str) -> StoredWeatherReport | None:
        return sqlite_latest(zip_code, self.database_path)

    def history(
        self,
        zip_code: str,
        start_at: datetime,
        end_before: datetime,
        page: int,
        page_size: int,
    ) -> tuple[list[StoredWeatherReport], int]:
        return sqlite_history(
            zip_code,
            start_at,
            end_before,
            page,
            page_size,
            self.database_path,
        )


def create_store() -> WeatherStore:
    """Create the storage implementation selected by the environment."""

    if config.STORAGE_BACKEND == "sqlite":
        return SQLiteWeatherStore()
    if config.STORAGE_BACKEND == "azure_table":
        return AzureTableWeatherStore()
    raise RuntimeError("WEATHER_STORAGE_BACKEND must be 'sqlite' or 'azure_table'")


STORE = create_store()


def initialize_storage() -> None:
    STORE.initialize()


def save_report(report: WeatherReport) -> StoredWeatherReport:
    return STORE.save(report)


def get_latest_report(zip_code: str) -> StoredWeatherReport | None:
    return STORE.latest(zip_code)


def get_weather_history(
    zip_code: str,
    start_at: datetime,
    end_before: datetime,
    page: int,
    page_size: int,
) -> tuple[list[StoredWeatherReport], int]:
    return STORE.history(zip_code, start_at, end_before, page, page_size)
