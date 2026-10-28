from pydantic import BaseModel


class MatchSummary(BaseModel):
    match_id: str
    champion: str
    win: bool
    kills: int
    deaths: int
    assists: int
    cs: int
    duration_seconds: int
    game_start: int          # NEW

    model_config = {"from_attributes": True}   # NEW: lets Pydantic read ORM objects


class PlayerMatches(BaseModel):
    game_name: str
    tag_line: str
    matches: list[MatchSummary]

class Summary(BaseModel):
    games: int
    wins: int
    win_rate: float
    kda: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    cs_per_min: float


class ChampionStat(BaseModel):
    champion: str
    games: int
    wins: int
    win_rate: float
    kda: float


class TrendPoint(BaseModel):
    match_id: str
    game_start: int
    kda: float
    kda_rolling: float


class HourStat(BaseModel):
    hour: int
    games: int
    wins: int
    win_rate: float


class PlayerStats(BaseModel):
    game_name: str
    tag_line: str
    summary: Summary
    champions: list[ChampionStat]
    kda_trend: list[TrendPoint]
    by_hour: list[HourStat]