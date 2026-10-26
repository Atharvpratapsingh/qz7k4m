import { useEffect, useState } from "react";
import { fetchDashboard, fetchHorizon } from "./api";
import KpiCards from "./components/KpiCards";
import { DailyChart, HourChart, HorizonChart, MainChart } from "./components/Charts";

// NEW: decision time options (delivery se ek din pehle, UK time)
const CUTOFFS = ["06:00", "08:00", "09:00", "10:00", "11:00", "12:00", "14:00", "16:00", "18:00"];

const RANGES = [
  { label: "Full month", from: "2026-01-02", to: "2026-02-01" },
  { label: "2–8 Jan", from: "2026-01-02", to: "2026-01-08" },
  { label: "9–15 Jan", from: "2026-01-09", to: "2026-01-15" },
  { label: "16–22 Jan", from: "2026-01-16", to: "2026-01-22" },
  { label: "23–29 Jan", from: "2026-01-23", to: "2026-01-29" },
  { label: "30 Jan–1 Feb", from: "2026-01-30", to: "2026-02-01" },
];

export default function App() {
  const [cutoff, setCutoff] = useState("09:00"); // NEW
  const [dash, setDash] = useState(null);
  const [horizon, setHorizon] = useState([]);
  const [error, setError] = useState(null); // NEW
  const [loading, setLoading] = useState(true); // NEW
  const [range, setRange] = useState(RANGES[1]);

  useEffect(() => {
    fetchHorizon().then(setHorizon).catch((e) => setError(e.message));
  }, []);

  // NEW: jab bhi cutoff badle, dashboard dobara load karo
  useEffect(() => {
    setLoading(true);
    fetchDashboard(cutoff)
      .then((d) => {
        setDash(d);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [cutoff]);

  const chartData = dash
    ? dash.timeseries.filter((r) => {
        const day = r.startTime.slice(0, 10);
        return day >= range.from && day <= range.to;
      })
    : [];

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>Wind Forecast Insight</h1>
          <p className="sub">
            GB national wind · Day-ahead purchase decisions made in January 2026 · Source: Elexon BMRS
          </p>
        </div>
        {/* NEW: dropdown */}
        <label className="control">
          <span>Decision time (day before delivery, UK)</span>
          <select value={cutoff} onChange={(e) => setCutoff(e.target.value)}>
            {CUTOFFS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      </header>

      {/* NEW: error message */}
      {error && <div className="error">Could not load data: {error}</div>}

      {dash && (
        <main className={loading ? "dim" : ""}>
          {/* NEW: explainer */}
          <p className="explainer">
            For every delivery hour we show the <b>latest wind forecast published before {cutoff} UK
            on the previous day</b>, the one you could actually have bought on. Forecasts published
            later are excluded, so accuracy is never overstated.
          </p>

          <KpiCards s={dash.summary} />

          <section className="card">
            <h2>Actual wind vs the forecast available at decision time</h2>
            <p className="hint">
              Shaded band: where actual wind landed 80% of the time, based on January&apos;s errors.
            </p>
            <div className="tabs">
              {RANGES.map((r) => (
                <button
                  key={r.label}
                  className={r.label === range.label ? "tab active" : "tab"}
                  onClick={() => setRange(r)}
                >
                  {r.label}
                </button>
              ))}
            </div>
            <MainChart data={chartData} />
          </section>

          <div className="grid2">
            <section className="card">
              <h2>How accuracy changes with lead time</h2>
              <p className="hint">All January forecasts, grouped by hours before delivery.</p>
              <HorizonChart data={horizon} decisionHours={dash.summary.meanHorizonHours} />
            </section>
            <section className="card">
              <h2>Error by hour of day</h2>
              <p className="hint">Which delivery hours need the biggest buffer.</p>
              <HourChart data={dash.byHour} />
            </section>
          </div>

          <section className="card">
            <h2>Daily bias</h2>
            <p className="hint">
              <span className="dot red" /> forecast too high (you were short) ·{" "}
              <span className="dot blue" /> forecast too low (you were long)
            </p>
            <DailyChart data={dash.daily} />
          </section>

          <footer className="footer">
            Error = forecast − actual. Forecasts are hourly (WINDFOR), actuals half-hourly (FUELHH,
            fuelType WIND); accuracy is measured on the hour where both exist.
          </footer>
        </main>
      )}

      {!dash && !error && <p className="loading">Loading January data…</p>}
    </div>
  );
}