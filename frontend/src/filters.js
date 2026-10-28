export const EMPTY_FILTERS = { champion: "", startDate: "", endDate: "" };

// <input type="date"> gives "YYYY-MM-DD". Adding a time without a "Z" makes JS
// parse it as LOCAL time. A bare "2026-10-01" would be parsed as UTC midnight,
// which is off by hours for most people.
export const startOfDayMs = (d) => new Date(`${d}T00:00:00`).getTime();
export const endOfDayMs = (d) => new Date(`${d}T23:59:59.999`).getTime();

// Same rules as the backend, used to filter the match table on the client
export function filterMatches(matches, { champion, startDate, endDate }) {
  const start = startDate ? startOfDayMs(startDate) : -Infinity;
  const end = endDate ? endOfDayMs(endDate) : Infinity;
  return matches.filter(
    (m) =>
      (!champion || m.champion === champion) &&
      m.game_start >= start &&
      m.game_start <= end,
  );
}