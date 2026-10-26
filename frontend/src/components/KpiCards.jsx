import { mw, signedMw } from "../format";

// Upar ke 5 numbers, trader ki bhasha mein
export default function KpiCards({ s }) {
  const cards = [
    {
      label: "Typical forecast miss",
      value: mw(s.mae),
      note: `${s.maePct}% of average wind output (MAE)`,
    },
    {
      label: "Systematic bias",
      value: signedMw(s.bias),
      note: s.bias > 0 ? "Forecast sits above actual wind" : "Forecast sits below actual wind",
      tone: s.bias > 0 ? "warn" : "ok",
    },
    {
      label: "Hours wind came in short",
      value: `${s.shareOverForecast}%`,
      note: "Actual wind lower than the forecast you bought on",
      tone: s.shareOverForecast > 60 ? "warn" : "ok",
    },
    {
      label: "80% of hours, actual vs forecast",
      value: `${signedMw(-s.p90Error)} to ${signedMw(-s.p10Error)}`,
      note: "Range to hold as a buffer (P10 to P90)",
      small: true,
    },
    {
      label: "Average lead time",
      value: `${s.meanHorizonHours} h`,
      note: `${s.count} delivery hours analysed`,
    },
  ];

  return (
    <div className="kpis">
      {cards.map((c) => (
        <div key={c.label} className={`kpi ${c.tone || ""}`}>
          <div className="kpi-label">{c.label}</div>
          <div className={`kpi-value ${c.small ? "small" : ""}`}>{c.value}</div>
          <div className="kpi-note">{c.note}</div>
        </div>
      ))}
    </div>
  );
}