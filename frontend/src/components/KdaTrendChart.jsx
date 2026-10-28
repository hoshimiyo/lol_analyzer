import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const shortDate = (ms) =>
  new Date(ms).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export function KdaTrendChart({ data }) {
  if (data.length < 2) {
    return <p className="muted">Not enough games for a KDA trend.</p>;
  }

  return (
    <section>
      <h3>KDA trend</h3>
      <div className="chart">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="game_start" tickFormatter={shortDate} minTickGap={40} />
            <YAxis />
            <Tooltip
              labelFormatter={(ms) => new Date(ms).toLocaleString()}
              formatter={(v) => v.toFixed(2)}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="kda"
              name="KDA"
              stroke="#8884d8"
              strokeOpacity={0.5}
              dot={{ r: 2 }}
            />
            <Line
              type="monotone"
              dataKey="kda_rolling"
              name="5-game average"
              stroke="#2ea043"
              strokeWidth={2.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}