from datetime import time

import pandas as pd

from app.analysis import join_with_actuals, select_decision_forecasts, summary_metrics


def make_df(rows):
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    return df


# Target: 10 Jan 12:00. Decision: 9 Jan 09:00 UK (January mein = UTC)
FORECASTS = make_df(
    [
        ("2026-01-10T12:00Z", "2026-01-08T22:30Z", 1000),  # purana, available
        ("2026-01-10T12:00Z", "2026-01-09T07:30Z", 2000),  # cutoff se pehle ka latest
        ("2026-01-10T12:00Z", "2026-01-09T09:30Z", 3000),  # cutoff ke baad: ignore hona chahiye
    ]
)


def test_picks_latest_forecast_before_cutoff():
    out = select_decision_forecasts(FORECASTS, time(9, 0))
    assert len(out) == 1
    assert out.loc[0, "forecast"] == 2000


def test_never_uses_forecast_published_after_cutoff():
    out = select_decision_forecasts(FORECASTS, time(9, 0))
    assert (out["publishTime"] <= pd.Timestamp("2026-01-09T09:00Z")).all()


def test_later_cutoff_uses_newer_forecast():
    out = select_decision_forecasts(FORECASTS, time(10, 0))
    assert out.loc[0, "forecast"] == 3000


def test_horizon_hours():
    out = select_decision_forecasts(FORECASTS, time(9, 0))
    # 9 Jan 07:30 se 10 Jan 12:00 = 28.5 ghante
    assert out.loc[0, "horizonHours"] == 28.5


def test_error_sign_and_metrics():
    selected = select_decision_forecasts(FORECASTS, time(9, 0))
    actuals = make_df([("2026-01-10T12:00Z", "2026-01-10T12:30Z", 1500)])
    joined = join_with_actuals(selected, actuals)
    # forecast 2000, actual 1500 -> +500 (over-forecast)
    assert joined.loc[0, "error"] == 500
    s = summary_metrics(joined)
    assert s["mae"] == 500
    assert s["bias"] == 500
    assert s["shareOverForecast"] == 100