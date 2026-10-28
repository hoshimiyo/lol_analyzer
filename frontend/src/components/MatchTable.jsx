function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function MatchTable({ matches }) {
  if (matches.length === 0) {
    return <p className="muted">No ranked solo/duo matches found.</p>;
  }

  return (
    <section>
      <h3>Recent matches</h3>
      <table>
        <thead>
          <tr>
            <th>Result</th>
            <th>Champion</th>
            <th>K / D / A</th>
            <th>CS</th>
            <th>Duration</th>
            <th>Played</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((m) => (
            <tr key={m.match_id} className={m.win ? "win" : "loss"}>
              <td>{m.win ? "Win" : "Loss"}</td>
              <td>{m.champion}</td>
              <td>
                {m.kills} / {m.deaths} / {m.assists}
              </td>
              <td>
                {m.cs} ({(m.cs / (m.duration_seconds / 60)).toFixed(1)}/min)
              </td>
              <td>{formatDuration(m.duration_seconds)}</td>
              <td>{new Date(m.game_start).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}