from datetime import time
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import analysis
from .data import load_actuals, load_forecasts

app = FastAPI(title="Wind Forecast Insight API")

# React alag port pe chalega, use API call karne ki permission
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


def parse_cutoff(value):
    """'09:00' jaisa text -> time object. Galat format pe 400 error."""
    try:
        hh, mm = value.split(":")
        return time(int(hh), int(mm))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="cutoff must look like HH:MM")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@lru_cache(maxsize=48)
def _dashboard(cutoff):
    actuals = load_actuals()
    forecasts = load_forecasts()

    selected = analysis.select_decision_forecasts(forecasts, cutoff)
    joined = analysis.join_with_actuals(selected, actuals)
    summary = analysis.summary_metrics(joined)

    return {
        "cutoff": cutoff.strftime("%H:%M"),
        "summary": summary,
        "byHour": analysis.error_by_hour_of_day(joined),
        "daily": analysis.daily_metrics(joined),
        "timeseries": analysis.timeseries(
            joined, actuals, summary["p10Error"], summary["p90Error"]
        ),
    }


@app.get("/api/dashboard")
def dashboard(cutoff: str = Query("09:00", description="Decision time on D-1, UK, HH:MM")):
    return _dashboard(parse_cutoff(cutoff))


@lru_cache(maxsize=1)
def _horizon():
    return analysis.error_by_horizon(load_forecasts(), load_actuals())


@app.get("/api/horizon")
def horizon():
    return _horizon()