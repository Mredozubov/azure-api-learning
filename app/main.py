"""FastAPI entry point for the Brooklyn weather application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, time, timedelta
from math import ceil
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import LOCATION_NAME, TIMEZONE, ZIP_CODE
from app.display import (
    aqi_status,
    eastern_time,
    report_matches_search,
    temperature_chart,
    time_ago,
    uv_status,
)
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
    docs_url=None,
)

APP_DIRECTORY = Path(__file__).parent
app.mount("/static", StaticFiles(directory=APP_DIRECTORY / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIRECTORY / "templates")
templates.env.globals["weather_label"] = weather_label
templates.env.globals["eastern_time"] = eastern_time
templates.env.globals["aqi_status"] = aqi_status
templates.env.globals["uv_status"] = uv_status


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
def api_documentation() -> HTMLResponse:
    """Show Swagger API documentation with a return-to-website link."""

    swagger = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API documentation",
    )
    back_link_style = """
    <style>
      .weather-back { display:block; padding:12px 18px; color:white;
        background:#093f4c; font:600 14px system-ui; text-decoration:none; }
      .weather-back:hover { background:#0d6173; }
    </style>
    """
    html = swagger.body.decode().replace(
        "</head>", f"{back_link_style}</head>"
    )
    html = html.replace(
        "<body>", '<body><a class="weather-back" href="/">← Current weather</a>'
    )
    return HTMLResponse(html)


@app.get("/", response_class=HTMLResponse, tags=["Pages"])
def read_home(request: Request) -> HTMLResponse:
    """Show the newest weather report or a useful empty state."""

    report = get_latest_report(ZIP_CODE)
    chart = None
    if report:
        chart_reports, _ = get_weather_history(
            ZIP_CODE,
            report.observed_at - timedelta(hours=23),
            report.observed_at + timedelta(hours=1),
            1,
            24,
        )
        chart = temperature_chart(chart_reports)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "report": report,
            "last_updated_age": time_ago(report.collected_at) if report else None,
            "temperature_chart": chart,
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
    q: Annotated[str, Query(max_length=100)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
) -> HTMLResponse:
    """Search every displayed history category with one text field."""

    query = q.strip()
    start_at = datetime(1970, 1, 1, tzinfo=UTC)
    end_before = datetime.now(UTC) + timedelta(days=1)
    if query:
        all_reports, _ = get_weather_history(
            ZIP_CODE, start_at, end_before, 1, 1_000_000
        )
        matching = [
            report
            for report in all_reports
            if report_matches_search(report, query)
        ]
        total = len(matching)
        offset = (page - 1) * 25
        reports = matching[offset : offset + 25]
    else:
        reports, total = get_weather_history(
            ZIP_CODE, start_at, end_before, page, 25
        )
    total_pages = ceil(total / 25)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "reports": reports,
            "query": query,
            "page": page,
            "total": total,
            "total_pages": total_pages,
        },
    )
