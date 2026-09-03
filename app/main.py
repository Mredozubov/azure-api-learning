"""FastAPI entry point for the Brooklyn weather application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, time, timedelta
from math import ceil
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import LOCATION_NAME, TIMEZONE, ZIP_CODE
from app.display import time_ago
from app.models import StoredWeatherReport, WeatherHistory
from app.storage import get_latest_report, get_weather_history, initialize_storage
from app.weather_codes import weather_label


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Prepare local persistence before serving requests."""

    initialize_storage()
    yield


app = FastAPI(
    title="Brooklyn Weather API",
    description="Hourly weather history for Brooklyn, New York ZIP code 11234.",
    version="0.2.0",
    lifespan=lifespan,
)

APP_DIRECTORY = Path(__file__).parent
app.mount("/static", StaticFiles(directory=APP_DIRECTORY / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIRECTORY / "templates")
templates.env.globals["weather_label"] = weather_label


@app.get("/", response_class=HTMLResponse, tags=["Pages"])
def read_home(request: Request) -> HTMLResponse:
    """Show the newest weather report or a useful empty state."""

    report = get_latest_report(ZIP_CODE)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "report": report,
            "last_updated_age": time_ago(report.collected_at) if report else None,
        },
    )


@app.get("/health", tags=["General"])
def health_check() -> dict[str, str]:
    """Report whether the application is available."""

    return {"status": "healthy"}


@app.get(
    "/api/weather/latest",
    response_model=StoredWeatherReport,
    tags=["Weather"],
)
def read_latest_weather() -> StoredWeatherReport:
    """Return the newest collected weather report."""

    report = get_latest_report(ZIP_CODE)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No weather reports exist yet. Run python -m app.collector.",
        )
    return report


@app.get(
    "/api/weather/history",
    response_model=WeatherHistory,
    tags=["Weather"],
)
def read_weather_history(
    start: Annotated[date, Query(description="First local calendar date")],
    end: Annotated[date, Query(description="Last local calendar date")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> WeatherHistory:
    """Search stored reports using inclusive Brooklyn calendar dates."""

    if end < start:
        raise HTTPException(
            status_code=400,
            detail="The end date must be on or after the start date.",
        )
    local_zone = ZoneInfo(TIMEZONE)
    start_at = datetime.combine(start, time.min, local_zone).astimezone(UTC)
    end_before = datetime.combine(
        end + timedelta(days=1), time.min, local_zone
    ).astimezone(UTC)
    reports, total = get_weather_history(
        ZIP_CODE, start_at, end_before, page, page_size
    )
    return WeatherHistory(
        reports=reports,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size),
    )


@app.get("/history", response_class=HTMLResponse, tags=["Pages"])
def read_history_page(
    request: Request,
    start: date | None = None,
    end: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
) -> HTMLResponse:
    """Show a searchable table of collected weather reports."""

    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    selected_end = end or today
    selected_start = start or (selected_end - timedelta(days=7))
    error = None
    reports: list[StoredWeatherReport] = []
    total = 0
    total_pages = 0
    if selected_end < selected_start:
        error = "The end date must be on or after the start date."
    else:
        local_zone = ZoneInfo(TIMEZONE)
        start_at = datetime.combine(
            selected_start, time.min, local_zone
        ).astimezone(UTC)
        end_before = datetime.combine(
            selected_end + timedelta(days=1), time.min, local_zone
        ).astimezone(UTC)
        reports, total = get_weather_history(
            ZIP_CODE, start_at, end_before, page, 25
        )
        total_pages = ceil(total / 25)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "reports": reports,
            "start": selected_start.isoformat(),
            "end": selected_end.isoformat(),
            "page": page,
            "total": total,
            "total_pages": total_pages,
            "error": error,
        },
    )
