from datetime import date, time, timedelta

import numpy as np
import pandas as pd

UK_TZ = "Europe/London"

# Jinki purchase decision January mein hui
FIRST_DELIVERY_DAY = date(2026, 1, 2)
LAST_DELIVERY_DAY = date(2026, 2, 1)


def delivery_day(ts):
    """UTC time ko UK ki local date mein badlo."""
    return ts.dt.tz_convert(UK_TZ).dt.date


def decision_time_utc(days, cutoff):
    """Har delivery day D ke liye: D-1 ko cutoff time (UK), UTC mein."""
    local = pd.to_datetime(
        [f"{d - timedelta(days=1)} {cutoff.strftime('%H:%M')}" for d in days]
    ).tz_localize(UK_TZ)
    return pd.Series(local.tz_convert("UTC"), index=days.index)


def select_decision_forecasts(forecasts, cutoff):
    """Har hour ke liye: decision time se pehle bana LATEST forecast."""
    f = forecasts.copy()

    # 1. Delivery day nikalo, sirf January wale din rakho
    f["deliveryDay"] = delivery_day(f["startTime"])
    f = f[(f["deliveryDay"] >= FIRST_DELIVERY_DAY) & (f["deliveryDay"] <= LAST_DELIVERY_DAY)]

    # 2. Har row ka decision time
    f["decisionTime"] = decision_time_utc(f["deliveryDay"], cutoff)

    # 3. Decision ke baad bane forecasts hatao (no look-ahead bias)
    f = f[f["publishTime"] <= f["decisionTime"]]

    # 4. Har hour ka latest rakho
    f = f.sort_values("publishTime").drop_duplicates("startTime", keep="last")
    f = f.sort_values("startTime")

    # Forecast kitne ghante pehle bana tha
    f["horizonHours"] = (f["startTime"] - f["publishTime"]).dt.total_seconds() / 3600

    f = f.rename(columns={"generation": "forecast"})
    return f[["startTime", "publishTime", "forecast", "horizonHours"]].reset_index(drop=True)


def join_with_actuals(selected, actuals):
    """Forecast hourly hai, actual half-hourly. Sirf jahan dono hain (har ghante), wahan compare."""
    a = actuals.rename(columns={"generation": "actual"})[["startTime", "actual"]]
    m = selected.merge(a, on="startTime", how="inner")
    m["error"] = m["forecast"] - m["actual"]  # + matlab forecast zyada tha
    return m


def summary_metrics(m):
    """Accuracy ke main numbers."""
    err = m["error"]
    p10, p90 = np.percentile(err, [10, 90])
    mae = err.abs().mean()
    return {
        "count": int(len(m)),
        "mae": round(float(mae), 1),
        "rmse": round(float(np.sqrt((err ** 2).mean())), 1),
        "bias": round(float(err.mean()), 1),
        "maePct": round(float(mae / m["actual"].mean() * 100), 1),
        "p10Error": round(float(p10), 1),
        "p90Error": round(float(p90), 1),
        "shareOverForecast": round(float((err > 0).mean() * 100), 1),
        "meanHorizonHours": round(float(m["horizonHours"].mean()), 1),
    }
def error_by_hour_of_day(m):
    """Din ke kis ghante forecast zyada galat hai."""
    h = m.assign(hour=m["startTime"].dt.tz_convert(UK_TZ).dt.hour)
    g = h.groupby("hour")["error"]
    out = pd.DataFrame({
        "mae": g.apply(lambda e: e.abs().mean()),
        "bias": g.mean(),
    }).reset_index()
    return out.round(1).to_dict(orient="records")


def daily_metrics(m):
    """Har delivery day ki accuracy, kharab din pakadne ke liye."""
    d = m.assign(day=delivery_day(m["startTime"]).astype(str))
    g = d.groupby("day")
    out = pd.DataFrame({
        "mae": g["error"].apply(lambda e: e.abs().mean()),
        "bias": g["error"].mean(),
        "meanActual": g["actual"].mean(),
        "meanForecast": g["forecast"].mean(),
    }).reset_index()
    return out.round(1).to_dict(orient="records")


def error_by_horizon(forecasts, actuals, max_hours=48, step=3):
    """
    SAARE forecasts use karke: forecast jitna pehle bana, utna kitna galat?
    Har 3 ghante ka bucket (0-3h, 3-6h, ...).
    """
    f = forecasts.copy()
    f["deliveryDay"] = delivery_day(f["startTime"])
    f = f[(f["deliveryDay"] >= FIRST_DELIVERY_DAY) & (f["deliveryDay"] <= LAST_DELIVERY_DAY)]
    f["horizonHours"] = (f["startTime"] - f["publishTime"]).dt.total_seconds() / 3600
    f = f[(f["horizonHours"] >= 0) & (f["horizonHours"] < max_hours)]

    a = actuals.rename(columns={"generation": "actual"})[["startTime", "actual"]]
    m = f.merge(a, on="startTime", how="inner")
    m["error"] = m["generation"] - m["actual"]
    m["horizonFrom"] = (m["horizonHours"] // step * step).astype(int)

    g = m.groupby("horizonFrom")["error"]
    out = pd.DataFrame({
        "mae": g.apply(lambda e: e.abs().mean()),
        "bias": g.mean(),
    }).reset_index()
    return out.round(1).to_dict(orient="records")


def timeseries(joined, actuals, p10, p90):
    """
    Main chart ka data: har 30 min ka actual + har ghante ka decision forecast
    + band (actual shayad kis range mein aayega, past error ke hisaab se).
    """
    a = actuals.copy()
    a["deliveryDay"] = delivery_day(a["startTime"])
    a = a[(a["deliveryDay"] >= FIRST_DELIVERY_DAY) & (a["deliveryDay"] <= LAST_DELIVERY_DAY)]
    a = a.rename(columns={"generation": "actual"})[["startTime", "actual"]]

    t = a.merge(joined[["startTime", "forecast", "publishTime"]], on="startTime", how="left")
    # actual = forecast - error, isliye range: forecast - P90 se forecast - P10 tak
    t["bandLow"] = t["forecast"] - p90
    t["bandHigh"] = t["forecast"] - p10

    t["startTime"] = t["startTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    t["publishTime"] = t["publishTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    t = t.astype(object).where(pd.notna(t), None)  # NaN ko None, taaki JSON mein null jaaye
    return t.to_dict(orient="records")