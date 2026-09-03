"""Azure Table Storage implementation used by the finished cloud build."""

from datetime import datetime
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableServiceClient, UpdateMode
from azure.identity import DefaultAzureCredential

from app.config import (
    AZURE_STORAGE_ACCOUNT_URL,
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_TABLE_NAME,
)
from app.database import utc_text
from app.models import StoredWeatherReport, WeatherReport


class AzureTableWeatherStore:
    """Store reports as Table entities with a direct pointer to the latest one."""

    def __init__(self, table_client: TableClient | None = None) -> None:
        self.table = table_client or self._create_client()

    @staticmethod
    def _create_client() -> TableClient:
        if AZURE_STORAGE_CONNECTION_STRING:
            service = TableServiceClient.from_connection_string(
                AZURE_STORAGE_CONNECTION_STRING
            )
            return service.get_table_client(AZURE_TABLE_NAME)
        if not AZURE_STORAGE_ACCOUNT_URL:
            raise RuntimeError(
                "AZURE_STORAGE_ACCOUNT_URL is required for Azure Table Storage"
            )
        return TableClient(
            endpoint=AZURE_STORAGE_ACCOUNT_URL,
            table_name=AZURE_TABLE_NAME,
            credential=DefaultAzureCredential(),
        )

    def initialize(self) -> None:
        """The Bicep deployment creates the table; runtime setup is unnecessary."""

    @staticmethod
    def _report_entity(report: WeatherReport) -> dict[str, Any]:
        values = report.model_dump(mode="json")
        entity = {key: value for key, value in values.items() if value is not None}
        entity.update(
            {
                "PartitionKey": f"{report.zip_code}_reports",
                "RowKey": utc_text(report.observed_at),
                "id": int(report.observed_at.timestamp()),
            }
        )
        return entity

    @staticmethod
    def _as_report(entity: dict[str, Any]) -> StoredWeatherReport:
        return StoredWeatherReport.model_validate(entity)

    def save(self, report: WeatherReport) -> StoredWeatherReport:
        """Upsert the hourly record and a cheap direct latest-record lookup."""

        entity = self._report_entity(report)
        self.table.upsert_entity(entity, mode=UpdateMode.REPLACE)
        latest = dict(entity)
        latest["PartitionKey"] = f"{report.zip_code}_system"
        latest["RowKey"] = "latest"
        self.table.upsert_entity(latest, mode=UpdateMode.REPLACE)
        return self._as_report(entity)

    def latest(self, zip_code: str) -> StoredWeatherReport | None:
        """Read the latest-record pointer without scanning history."""

        try:
            entity = self.table.get_entity(f"{zip_code}_system", "latest")
        except ResourceNotFoundError:
            return None
        return self._as_report(dict(entity))

    def history(
        self,
        zip_code: str,
        start_at: datetime,
        end_before: datetime,
        page: int,
        page_size: int,
    ) -> tuple[list[StoredWeatherReport], int]:
        """Read a small date range and apply the API's page-number contract."""

        query = "PartitionKey eq @partition and RowKey ge @start and RowKey lt @end"
        parameters = {
            "partition": f"{zip_code}_reports",
            "start": utc_text(start_at),
            "end": utc_text(end_before),
        }
        entities = list(self.table.query_entities(query, parameters=parameters))
        entities.sort(key=lambda entity: entity["RowKey"], reverse=True)
        total = len(entities)
        offset = (page - 1) * page_size
        reports = [
            self._as_report(dict(entity))
            for entity in entities[offset : offset + page_size]
        ]
        return reports, total
