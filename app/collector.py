"""Command-line entry point for collecting one weather report."""

from app.storage import save_report
from app.weather_client import OpenMeteoClient, WeatherProviderError


def collect_once(client: OpenMeteoClient | None = None) -> int:
    """Fetch and save one report, returning its database ID."""

    report = (client or OpenMeteoClient()).fetch_current()
    return save_report(report).id


def main() -> None:
    """Run a collection and print a human-friendly result."""

    try:
        report_id = collect_once()
    except WeatherProviderError as error:
        raise SystemExit(f"Collection failed: {error}") from error
    print(f"Saved weather report {report_id} for Brooklyn, NY 11234.")


if __name__ == "__main__":
    main()
