"""Tests for local scheduling, overlap protection, and recovery."""

import json
import logging

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.scheduler import JsonFormatter, build_scheduler, run_collection


def test_default_scheduler_runs_hourly_and_prevents_overlap() -> None:
    scheduler = build_scheduler(collector=lambda: 1)
    job = scheduler.get_job("hourly_weather_collection")

    assert isinstance(job.trigger, CronTrigger)
    assert job.max_instances == 1
    assert job.coalesce is True


def test_scheduler_accepts_short_test_interval() -> None:
    scheduler = build_scheduler(interval_seconds=0.05, collector=lambda: 1)
    job = scheduler.get_job("hourly_weather_collection")

    assert isinstance(job.trigger, IntervalTrigger)


def test_collection_failure_does_not_escape() -> None:
    def failing_collector() -> int:
        raise RuntimeError("provider unavailable")

    assert run_collection(failing_collector) is False
    assert run_collection(lambda: 42) is True


def test_json_formatter_includes_structured_fields() -> None:
    record = logging.LogRecord(
        name="weather.scheduler",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="weather_collection_failed",
        args=(),
        exc_info=None,
    )
    record.error = "provider unavailable"

    data = json.loads(JsonFormatter().format(record))

    assert data["level"] == "ERROR"
    assert data["event"] == "weather_collection_failed"
    assert data["error"] == "provider unavailable"
