# Wind Forecast Insight

A web app for a UK energy utility's day-ahead trading team. For January 2026 it shows:

1. **The latest wind forecast that was actually available when the purchase decision was made** (day before delivery, at a configurable cutoff time).
2. **How accurate that forecast was**, in numbers the team can plan buffers with.

**Live app:** https://qz7k4m-ezoj.vercel.app/
**Live API:** https://qz7k4m.vercel.app/api/health

Data: national GB wind generation from Elexon BMRS only: actuals from `FUELHH` (`fuelType = WIND`) and forecasts from `WINDFOR`.

---

## Key results (decision at 09:00 UK on the day before delivery)

| Metric | Value |
|---|---|
| Typical forecast miss (MAE) | ~2,023 MW (17.9% of mean wind output) |
| Bias (forecast − actual) | +1,746 MW: the forecast is systematically too high |
| Hours where actual wind came in below the forecast | 84.7% |
| 80% range of actual vs forecast (P10 to P90) | −4,154 MW to +426 MW |
| Average lead time of the forecast used | 28 h |

Error grows with lead time: ~1,650 MW at 0–3 h before delivery vs ~2,360 MW at 45–48 h.

---

## How the forecast is selected (core logic)

For every delivery hour on delivery day **D**:

1. Decision time = **D−1 at the cutoff** (default 09:00, UK local time; selectable in the UI).
2. Keep only forecasts with `publishTime <= decision time`.
3. Of those, take the **latest** one.

Forecasts published after the cutoff are never used. Using them would be **look-ahead bias** and would make the forecast look more accurate than it really was for the trader. This rule is covered by unit tests.

**Assumptions**
- "Decisions made in January 2026" = delivery days **2 Jan to 1 Feb 2026**.
- `WINDFOR` is hourly, `FUELHH` is half-hourly. Accuracy is measured only on the hour, where both exist (no interpolation).
- Error = forecast − actual. Positive means the team would have been **short** of power.

---

## Repository structure

```
.
├── backend/
│   ├── app/
│   │   ├── analysis.py      # Core logic: forecast selection + accuracy metrics (pure pandas functions)
│   │   ├── data.py          # Loads the cached CSVs once (lru_cache)
│   │   └── main.py          # FastAPI endpoints; also serves the built React app inside Docker
│   ├── data/
│   │   ├── actuals.csv      # FUELHH WIND, Jan 2026 (cached)
│   │   └── forecasts.csv    # WINDFOR, all forecasts published 29 Dec – 1 Feb (cached)
│   ├── scripts/
│   │   └── fetch_data.py    # Downloads the data from Elexon in chunks and saves the CSVs
│   ├── tests/
│   │   └── test_analysis.py # Unit tests (no look-ahead, error sign, metrics)
│   ├── pyproject.toml       # Dependencies + Vercel entrypoint
│   └── requirements.txt     # Dependencies for local / Docker
├── frontend/
│   └── src/
│       ├── App.jsx          # Page layout and state (cutoff, date range), calls the API
│       ├── api.js           # All backend calls in one place (base URL from VITE_API_BASE)
│       ├── format.js        # MW and UK date formatting
│       └── components/
│           ├── KpiCards.jsx # Headline numbers
│           └── Charts.jsx   # Recharts: actual vs forecast, lead time, hour of day, daily bias
├── Dockerfile               # Multi-stage: builds React, then runs FastAPI serving API + UI
└── .dockerignore
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/health` | Liveness check |
| `GET /api/dashboard?cutoff=09:00` | Summary metrics, error by hour, daily metrics and chart time series for one cutoff |
| `GET /api/horizon` | Accuracy vs forecast lead time (all forecasts) |

Interactive docs: `/docs` (Swagger), e.g. https://qz7k4m.vercel.app/docs

---

## How to run

### Option 1: Docker (single container, API + UI)
```bash
docker build -t wind-forecast .
docker run -p 8000:8000 wind-forecast
```
Open http://localhost:8000

### Option 2: Local development
**Backend** (Python 3.12+)
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
**Frontend** (Node 20+), in a second terminal
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (Vite proxies `/api` to port 8000).

### Tests
```bash
cd backend
python -m pytest
```

### Refresh the data (optional)
```bash
cd backend
python scripts/fetch_data.py
```

---

## Design notes
- **Cached data:** the analysis window is fixed (January 2026), so data is downloaded once and stored as CSV. The app is fast and does not depend on Elexon being available.
- **Separation of concerns:** all business logic lives in `analysis.py` as pure functions; `main.py` is a thin API layer. This keeps the logic easy to test.
- **Deployment:** two Vercel projects from this repo: `backend/` (FastAPI as a Python function) and `frontend/` (Vite static build, `VITE_API_BASE` points to the API).

## Use of AI tools
I used Claude (Anthropic) as a coding assistant while building this project: to explore the Elexon API, structure the analysis, write and debug code, and troubleshoot the Vercel deployment. I reviewed, ran and tested all code myself, and I can explain every part of it.