const pct = (n) => `${Math.round(n * 100)}%`;

export function StatsSummary({ stats }) {
  const { summary: s, champions } = stats;

  const cards = [
    { label: "Games", value: String(s.games) },
    { label: "Win rate", value: pct(s.win_rate) },
    { label: "KDA", value: s.kda.toFixed(2) },
    {
      label: "Avg K / D / A",
      value: `${s.avg_kills.toFixed(1)} / ${s.avg_deaths.toFixed(1)} / ${s.avg_assists.toFixed(1)}`,
    },
    { label: "CS / min", value: s.cs_per_min.toFixed(1) },
  ];

  return (
    <section>
      <h2>
        {stats.game_name}#{stats.tag_line}
      </h2>

      <div className="cards">
        {cards.map((c) => (
          <div key={c.label} className="card">
            <div className="muted">{c.label}</div>
            <div className="value">{c.value}</div>
          </div>
        ))}
      </div>

      <h3>Most played</h3>
      <table>
        <thead>
          <tr>
            <th>Champion</th>
            <th>Games</th>
            <th>Win rate</th>
            <th>KDA</th>
          </tr>
        </thead>
        <tbody>
          {champions.map((c) => (
            <tr key={c.champion}>
              <td>{c.champion}</td>
              <td>{c.games}</td>
              <td>{pct(c.win_rate)}</td>
              <td>{c.kda.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}