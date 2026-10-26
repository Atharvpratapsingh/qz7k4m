from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Decisions in January -> delivery days 2 Jan to 1 Feb. Thoda extra le rahe hain.
ACTUALS_FROM = date(2026, 1, 1)
ACTUALS_TO = date(2026, 2, 2)

# 2 Jan ka forecast 29-31 Dec ko bhi bana ho sakta hai, isliye pehle se shuru
FORECAST_FROM = datetime(2025, 12, 29, tzinfo=timezone.utc)
FORECAST_TO = datetime(2026, 2, 2, tzinfo=timezone.utc)


def get_json(url, params):
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()  # error aaye to yahin ruk jao, chupchaap galat data mat lo
    return resp.json()


def fetch_actuals():
    rows = []
    day = ACTUALS_FROM
    while day <= ACTUALS_TO:
        chunk_end = min(day + timedelta(days=6), ACTUALS_TO)  # 7 din ka chunk
        print("  actuals", day, "->", chunk_end)
        rows += get_json(f"{BASE_URL}/FUELHH/stream", {
            "settlementDateFrom": day.isoformat(),
            "settlementDateTo": chunk_end.isoformat(),
            "fuelType": "WIND",
        })
        day = chunk_end + timedelta(days=1)

    df = pd.DataFrame(rows)[["startTime", "publishTime", "generation"]]
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    # Ek slot do baar aaya ho to latest rakho
    df = df.sort_values("publishTime").drop_duplicates("startTime", keep="last")
    return df.sort_values("startTime").reset_index(drop=True)


def fetch_forecasts():
    rows = []
    start = FORECAST_FROM
    while start < FORECAST_TO:
        end = start + timedelta(days=1)  # 1 din ka chunk
        print("  forecasts published", start.date())
        rows += get_json(f"{BASE_URL}/WINDFOR/stream", {
            "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%MZ"),
            "publishDateTimeTo": end.strftime("%Y-%m-%dT%H:%MZ"),
        })
        start = end

    df = pd.DataFrame(rows)[["startTime", "publishTime", "generation"]]
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df.drop_duplicates(["startTime", "publishTime"])
    return df.sort_values(["startTime", "publishTime"]).reset_index(drop=True)


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)

    print("Downloading actuals...")
    actuals = fetch_actuals()
    actuals.to_csv(DATA_DIR / "actuals.csv", index=False)
    print("  saved", len(actuals), "rows")

    print("Downloading forecasts...")
    forecasts = fetch_forecasts()
    forecasts.to_csv(DATA_DIR / "forecasts.csv", index=False)
    print("  saved", len(forecasts), "rows")