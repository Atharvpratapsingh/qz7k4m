from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _read(name):
    df = pd.read_csv(DATA_DIR / name)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    return df


@lru_cache(maxsize=1)
def load_actuals():
    return _read("actuals.csv")


@lru_cache(maxsize=1)
def load_forecasts():
    return _read("forecasts.csv")