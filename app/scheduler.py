"""Run the local weather collector once per hour."""

import argparse
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.collector import collect_once


LOGGER = logging.getLogger("weather.scheduler")


class JsonFormatter(logging.Formatter):
    """Format scheduler events as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        message: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in ("report_id", "error"):
            value = getattr(record, field, None)
            if value is not None:
                message[field] = value
        return json.dumps(message)


def configure_logging() -> None:
    """Send concise structured scheduler logs to the terminal."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    LOGGER.handlers.clear()
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def run_collection(collector: Callable[[], int] = collect_once) -> bool:
    """Run once and contain failures so later scheduled runs still happen."""

    try:
        report_id = collector()
    except Exception as error:  # The scheduler must survive provider/database errors.
        LOGGER.error(
            "weather_collection_failed",
            extra={"error": str(error)},
        )
        return False
    LOGGER.info(
        "weather_collection_succeeded",
        extra={"report_id": report_id},
    )
    return True


def build_scheduler(
    interval_seconds: float | None = None,
    collector: Callable[[], int] = collect_once,
) -> BlockingScheduler:
    """Create an hourly scheduler, or a fast interval scheduler for tests."""

    scheduler = BlockingScheduler(timezone="UTC")
    trigger = (
        IntervalTrigger(seconds=interval_seconds)
        if interval_seconds is not None
        else CronTrigger(minute=0, timezone="UTC")
    )
    scheduler.add_job(
        run_collection,
        trigger=trigger,
        kwargs={"collector": collector},
        id="hourly_weather_collection",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    return scheduler


def parse_args() -> argparse.Namespace:
    """Read the optional development-only interval override."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interval-seconds",
        type=float,
        help="Development/testing override; omit for hourly collection.",
    )
    return parser.parse_args()


def main() -> None:
    """Start the scheduler until the user presses Ctrl+C."""

    args = parse_args()
    if args.interval_seconds is not None and args.interval_seconds <= 0:
        raise SystemExit("--interval-seconds must be greater than zero")
    configure_logging()
    scheduler = build_scheduler(args.interval_seconds)
    LOGGER.info("weather_scheduler_started")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("weather_scheduler_stopped")


if __name__ == "__main__":
    main()
