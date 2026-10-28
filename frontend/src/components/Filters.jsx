import { EMPTY_FILTERS } from "../filters";

export function Filters({ filters, onChange, champions }) {
  const set = (key) => (e) => onChange({ ...filters, [key]: e.target.value });
  const active = filters.champion || filters.startDate || filters.endDate;

  return (
    <div className="filters">
      <label>
        Champion
        <select value={filters.champion} onChange={set("champion")}>
          <option value="">All</option>
          {champions.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <label>
        From
        <input
          type="date"
          value={filters.startDate}
          max={filters.endDate || undefined}
          onChange={set("startDate")}
        />
      </label>

      <label>
        To
        <input
          type="date"
          value={filters.endDate}
          min={filters.startDate || undefined}
          onChange={set("endDate")}
        />
      </label>

      {active && (
        <button type="button" onClick={() => onChange(EMPTY_FILTERS)}>
          Clear
        </button>
      )}
    </div>
  );
}