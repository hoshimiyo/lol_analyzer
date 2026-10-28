import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PERIODS = [
  { label: "Night (0–5)", from: 0, to: 5 },
  { label: "Morning (6–11)", from: 6, to: 11 },
  { label: "Afternoon (12–17)", from: 12, to: 17 },
  { label: "Evening (18–23)", from: 18, to: 23 },
];

// 24 hourly buckets have 1-2 games each and look like noise,
// so merge them into four parts of the day.
function groupByPeriod(byHour) {
  return PERIODS.map(({ label, from, to }) => {
    const rows = byHour.filter((h) => h.hour >= from && h.hour <= to);
    const games = rows.reduce((n, h) => n + h.games, 0);
    const wins = rows.reduce((n, h) => n + h.wins, 0);
    return { label, games, wins, winRate: games ? (wins / games) * 100 : null };
  });
}

export function WinRateByTimeChart({ byHour }) {
  const data = groupByPeriod(byHour);

  return (
    <section>
      <h3>Win rate by time of day</h3>
      <div className="chart">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="label" />
            <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
            <ReferenceLine y={50} strokeDasharray="4 4" />
            <Tooltip
              formatter={(v, _name, item) =>
                v == null
                  ? "No games"
                  : `${Math.round(v)}% (${item.payload.wins}/${item.payload.games} games)`
              }
            />
            <Bar dataKey="winRate" name="Win rate" fill="#8884d8" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="muted">
        Times are in your local timezone. Periods with few games are noisy, so check
        the game counts in the tooltip.
      </p>
    </section>
  );
}