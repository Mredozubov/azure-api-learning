"""Azure Functions entry points for the website and hourly collector."""

import logging

import azure.functions as func

from app.main import app as fastapi_app
from app.scheduler import configure_logging, run_collection


configure_logging()


app = func.AsgiFunctionApp(
    app=fastapi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS,
)


@app.schedule(
    schedule="0 0 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def hourly_weather_collection(timer: func.TimerRequest) -> None:
    """Ask Azure to collect weather at the start of every UTC hour."""

    if timer.past_due:
        logging.warning("weather_timer_is_past_due")
    run_collection()
