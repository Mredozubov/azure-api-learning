"""Tests for the Azure timer entry point without contacting Azure."""

import function_app


class FakeTimer:
    past_due = False


def test_azure_timer_runs_shared_collector(monkeypatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(function_app, "run_collection", lambda: calls.append(True))

    function_app.hourly_weather_collection(FakeTimer())

    assert calls == [True]


def test_azure_timer_uses_configured_schedule_and_monitor() -> None:
    timer_function = next(
        function
        for function in function_app.app.get_functions()
        if function.get_function_name() == "hourly_weather_collection"
    )
    timer_binding = timer_function.get_bindings()[0].get_dict_repr()

    assert timer_binding["schedule"] == "%WEATHER_TIMER_SCHEDULE%"
    assert timer_binding["runOnStartup"] is False
    assert timer_binding["useMonitor"] is True
