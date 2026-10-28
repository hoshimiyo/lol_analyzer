import pandas as pd

from .schemas import MatchSummary


def _empty() -> dict:
    return {
        "summary": {
            "games": 0, "wins": 0, "win_rate": 0.0, "kda": 0.0,
            "avg_kills": 0.0, "avg_deaths": 0.0, "avg_assists": 0.0, "cs_per_min": 0.0,
        },
        "champions": [],
        "kda_trend": [],
        "by_hour": [],
    }


def compute_stats(matches: list[MatchSummary], tz: str = "UTC", top_champs: int = 5) -> dict:
    if not matches:
        return _empty()

    # 1. Build a DataFrame, oldest game first (trend charts read left to right)
    df = (
        pd.DataFrame([m.model_dump() for m in matches])
        .sort_values("game_start")
        .reset_index(drop=True)
    )

    # 2. Derived per-match columns
    df["minutes"] = df["duration_seconds"] / 60
    df["kda"] = (df["kills"] + df["assists"]) / df["deaths"].clip(lower=1)

    # 3. Overall summary
    total_deaths = max(int(df["deaths"].sum()), 1)
    summary = {
        "games": len(df),
        "wins": int(df["win"].sum()),
        "win_rate": float(df["win"].mean()),
        "kda": float((df["kills"].sum() + df["assists"].sum()) / total_deaths),
        "avg_kills": float(df["kills"].mean()),
        "avg_deaths": float(df["deaths"].mean()),
        "avg_assists": float(df["assists"].mean()),
        "cs_per_min": float(df["cs"].sum() / df["minutes"].sum()),
    }

    # 4. Per-champion breakdown
    by_champ = df.groupby("champion").agg(
        games=("win", "size"),
        wins=("win", "sum"),
        kills=("kills", "sum"),
        deaths=("deaths", "sum"),
        assists=("assists", "sum"),
    )
    by_champ["win_rate"] = by_champ["wins"] / by_champ["games"]
    by_champ["kda"] = (by_champ["kills"] + by_champ["assists"]) / by_champ["deaths"].clip(lower=1)
    champions = (
        by_champ.sort_values(["games", "win_rate"], ascending=False)
        .head(top_champs)
        .reset_index()[["champion", "games", "wins", "win_rate", "kda"]]
        .to_dict("records")
    )

    # 5. KDA trend with a 5-game rolling average
    df["kda_rolling"] = df["kda"].rolling(5, min_periods=1).mean()
    kda_trend = df[["match_id", "game_start", "kda", "kda_rolling"]].to_dict("records")

    # 6. Win rate by hour of day, in the caller's timezone
    local = pd.to_datetime(df["game_start"], unit="ms", utc=True).dt.tz_convert(tz)
    df["hour"] = local.dt.hour
    by_hour = df.groupby("hour").agg(games=("win", "size"), wins=("win", "sum")).reset_index()
    by_hour["win_rate"] = by_hour["wins"] / by_hour["games"]

    return {
        "summary": summary,
        "champions": champions,
        "kda_trend": kda_trend,
        "by_hour": by_hour.to_dict("records"),
    }