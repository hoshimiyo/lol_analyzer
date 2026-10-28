import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchMatches, fetchStats } from "./api";
import { EMPTY_FILTERS, filterMatches } from "./filters";
import { Filters } from "./components/Filters";
import { KdaTrendChart } from "./components/KdaTrendChart";
import { MatchTable } from "./components/MatchTable";
import { SearchForm } from "./components/SearchForm";
import { StatsSummary } from "./components/StatsSummary";
import { WinRateByTimeChart } from "./components/WinRateByTimeChart";

export default function App() {
  const [riotId, setRiotId] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const matches = useQuery({
    queryKey: ["matches", riotId],
    queryFn: () => fetchMatches(riotId),
    enabled: riotId !== null,
  });
  const stats = useQuery({
    queryKey: ["stats", riotId, filters],
    queryFn: () => fetchStats(riotId, filters),
    enabled: riotId !== null && matches.isSuccess,
    placeholderData: (previous, previousQuery) =>
      previousQuery?.queryKey[1] === riotId ? previous : undefined,
  });
  const champions = useMemo(
    () =>
      [...new Set((matches.data?.matches ?? []).map((m) => m.champion))].sort(),
    [matches.data],
  );
  const visibleMatches = useMemo(
    () => filterMatches(matches.data?.matches ?? [], filters),
    [matches.data, filters],
  );
  const error = matches.error ?? stats.error;
  function handleSearch(id) {
    setRiotId(id);
    setFilters(EMPTY_FILTERS);
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <h1>LoL Match Analyzer</h1>
          <p className="app-intro">
            Find the patterns in your ranked history that are worth changing.
          </p>
        </div>
        <p className="data-note">Public match data · evidence over guesswork</p>
      </header>
      <section className="search-panel" aria-labelledby="search-title">
        <div className="search-copy">
          <h2 id="search-title">Review a player</h2>
          <p>
            Search a Riot ID to sync recent ranked matches and surface the
            evidence.
          </p>
        </div>
        <SearchForm onSearch={handleSearch} loading={matches.isFetching} />
      </section>
      {matches.isLoading && (
        <p className="status-message">Fetching matches from Riot…</p>
      )}
      {error && (
        <p role="alert" className="error">
          {error.message}
        </p>
      )}
      {matches.data && (
        <Filters
          filters={filters}
          onChange={setFilters}
          champions={champions}
        />
      )}
      <div className="analysis-content" aria-live="polite">
        {stats.data &&
          (stats.data.summary.games === 0 ? (
            <p className="empty-state">
              No matches fit these filters. Try widening the date range.
            </p>
          ) : (
            <>
              <StatsSummary stats={stats.data} />
              <div className="chart-grid">
                <KdaTrendChart data={stats.data.kda_trend} />
                <WinRateByTimeChart byHour={stats.data.by_hour} />
              </div>
            </>
          ))}
        {matches.data && <MatchTable matches={visibleMatches} />}
      </div>
      <footer className="app-footer">
        <p className="disclaimer">
          "Lol-analyzer" isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved inproducing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
        </p>
      </footer>
    </main>
  );
}
