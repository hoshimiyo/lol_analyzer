import { endOfDayMs, startOfDayMs } from "./filters";


// Response shapes (they mirror the Pydantic schemas in the backend):
//   MatchSummary: { match_id, champion, win, kills, deaths, assists, cs, duration_seconds, game_start }
//   PlayerMatches: { game_name, tag_line, matches: MatchSummary[] }
//   PlayerStats: { game_name, tag_line, summary, champions, kda_trend, by_hour }
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // FastAPI sends {"detail": "..."}; validation errors send a list instead
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // body wasn't JSON, keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

const playerPath = (id) =>
  `/api/players/${encodeURIComponent(id.gameName)}/${encodeURIComponent(id.tagLine)}`;

export const fetchMatches = (id, count = 20) =>
  getJson(`${playerPath(id)}/matches?count=${count}`);

export const fetchStats = (id, filters = {}) => {
  const params = new URLSearchParams({
    tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  if (filters.champion) params.set("champion", filters.champion);
  if (filters.startDate) params.set("start", String(startOfDayMs(filters.startDate)));
  if (filters.endDate) params.set("end", String(endOfDayMs(filters.endDate)));
  return getJson(`${playerPath(id)}/stats?${params}`);
};

// "Name#TAG" -> { gameName, tagLine }, or null if the input is malformed
export function parseRiotId(input) {
  const i = input.lastIndexOf("#");
  if (i <= 0 || i === input.length - 1) return null;
  const gameName = input.slice(0, i).trim();
  const tagLine = input.slice(i + 1).trim();
  return gameName && tagLine ? { gameName, tagLine } : null;
}