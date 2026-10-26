import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { mw, ukDateTime, ukDay } from "../format";

// Saare charts ke colours ek jagah
const C = {
  actual: "#0f766e",
  forecast: "#ea580c",
  band: "#fdba74",
  bias: "#dc2626",
  under: "#2563eb",
  grid: "#e5e7eb",
};

// Y-axis label: 2500 -> "2.5k", 12000 -> "12k"
const kmw = (v) => `${(v / 1000).toFixed(Math.abs(v) < 10000 && v % 1000 !== 0 ? 1 : 0)}k`;

// 1. Actual vs decision-time forecast
export function MainChart({ data }) {
  // Har din raat 12 baje ek date label (poore month mein har 3rd din)
  const midnights = data.filter((d) => d.startTime.endsWith("T00:00:00Z")).map((d) => d.startTime);
  const ticks = midnights.length > 10 ? midnights.filter((_, i) => i % 3 === 0) : midnights;

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="startTime" ticks={ticks} tickFormatter={ukDay} />
        <YAxis tickFormatter={kmw} width={44} domain={[0, "auto"]} />
        <Tooltip
          labelFormatter={ukDateTime}
          formatter={(v, name) =>
            Array.isArray(v) ? [`${mw(v[0])} – ${mw(v[1])}`, name] : [mw(v), name]
          }
        />
        <Legend />
        <Area
          name="Likely range (80%)"
          dataKey={(d) => (d.bandLow == null ? null : [Math.max(0, d.bandLow), d.bandHigh])}
          fill={C.band}
          fillOpacity={0.35}
          stroke="none"
          connectNulls
          isAnimationActive={false}
        />
        <Line
          name="Forecast at decision time"
          dataKey="forecast"
          stroke={C.forecast}
          strokeWidth={2}
          dot={false}
          connectNulls
          isAnimationActive={false}
        />
        <Line
          name="Actual wind"
          dataKey="actual"
          stroke={C.actual}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
// 2. Lead time vs error: day-ahead decide karne ki keemat
export function HorizonChart({ data, decisionHours }) {
  // Bucket 0-3h ko 1.5 pe plot karo (beech mein)
  const rows = data.map((d) => ({ ...d, mid: d.horizonFrom + 1.5 }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows} margin={{ top: 20, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis
          dataKey="mid"
          type="number"
          domain={[0, 48]}
          ticks={[0, 6, 12, 18, 24, 30, 36, 42, 48]}
          tickFormatter={(h) => `${h}h`}
        />
        <YAxis tickFormatter={kmw} width={44} domain={[0, "auto"]} />
        <Tooltip
          labelFormatter={(h) => `${h - 1.5}–${h + 1.5} h before delivery`}
          formatter={(v, name) => [mw(v), name]}
        />
        <Legend />
        <ReferenceLine
          x={decisionHours}
          stroke="#475569"
          strokeDasharray="4 4"
          label={{ value: "Your decision", position: "top", fontSize: 12 }}
        />
        <Line name="Avg miss (MAE)" dataKey="mae" stroke={C.forecast} strokeWidth={2} />
        <Line name="Bias" dataKey="bias" stroke={C.bias} strokeDasharray="5 3" />
      </LineChart>
    </ResponsiveContainer>
  );
}

// 3. Din ke kis ghante forecast sabse zyada galat
export function HourChart({ data }) {
  const hh = (h) => `${String(h).padStart(2, "0")}:00`;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="hour" tickFormatter={hh} minTickGap={20} />
        <YAxis tickFormatter={kmw} width={44} />
        <Tooltip labelFormatter={(h) => `${hh(h)} UK`} formatter={(v, name) => [mw(v), name]} />
        <Legend />
        <Bar name="Avg miss (MAE)" dataKey="mae" fill={C.forecast} />
        <Bar name="Bias" dataKey="bias" fill={C.bias} fillOpacity={0.6} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// 4. Har din ka bias: laal = short, neela = long
export function DailyChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid stroke={C.grid} vertical={false} />
        <XAxis dataKey="day" tickFormatter={ukDay} minTickGap={20} />
        <YAxis tickFormatter={kmw} width={44} />
        <Tooltip labelFormatter={ukDay} formatter={(v, name) => [mw(v), name]} />
        <ReferenceLine y={0} stroke="#94a3b8" />
        <Bar name="Daily bias (forecast − actual)" dataKey="bias">
          {data.map((d) => (
            <Cell key={d.day} fill={d.bias > 0 ? C.bias : C.under} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}