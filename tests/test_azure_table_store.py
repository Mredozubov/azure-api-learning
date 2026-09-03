"""Tests for Azure storage behavior without contacting Azure."""

from datetime import UTC, datetime

from app.azure_table_store import AzureTableWeatherStore
from app.models import WeatherReport


class FakeTableClient:
    def __init__(self) -> None:
        self.entities: dict[tuple[str, str], dict] = {}

    def upsert_entity(self, entity: dict, **_kwargs) -> None:
        key = (entity["PartitionKey"], entity["RowKey"])
        self.entities[key] = dict(entity)

    def get_entity(self, partition_key: str, row_key: str) -> dict:
        return self.entities[(partition_key, row_key)]

    def query_entities(self, _query: str, parameters: dict) -> list[dict]:
        return [
            entity
            for entity in self.entities.values()
            if entity["PartitionKey"] == parameters["partition"]
            and parameters["start"] <= entity["RowKey"] < parameters["end"]
        ]


def make_report(hour: int) -> WeatherReport:
    return WeatherReport(
        observed_at=datetime(2026, 9, 3, hour, tzinfo=UTC),
        collected_at=datetime(2026, 9, 3, hour, 5, tzinfo=UTC),
        location_name="Brooklyn, NY 11234",
        zip_code="11234",
        temperature_f=float(hour),
    )


def test_azure_store_saves_history_and_latest_pointer() -> None:
    client = FakeTableClient()
    store = AzureTableWeatherStore(table_client=client)
    store.save(make_report(10))
    stored = store.save(make_report(11))

    latest = store.latest("11234")
    history, total = store.history(
        "11234",
        datetime(2026, 9, 3, tzinfo=UTC),
        datetime(2026, 9, 4, tzinfo=UTC),
        page=1,
        page_size=25,
    )

    assert latest is not None
    assert latest.id == stored.id
    assert latest.temperature_f == 11.0
    assert total == 2
    assert [report.temperature_f for report in history] == [11.0, 10.0]
