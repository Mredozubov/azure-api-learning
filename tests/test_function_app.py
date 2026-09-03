"""Tests for the Azure timer entry point without contacting Azure."""

import function_app


class FakeTimer:
    past_due = False


def test_azure_timer_runs_shared_collector(monkeypatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(function_app, "run_collection", lambda: calls.append(True))

    function_app.hourly_weather_collection(FakeTimer())

    assert calls == [True]
