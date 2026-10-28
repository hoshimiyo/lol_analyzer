import pytest

from app.schemas import MatchSummary
from app.stats import compute_stats

BASE = 1_700_000_000_000  # 2023-11-14 22:13:20 UTC

STATS = "/api/players/Faker/KR1/stats"
BASE_MS = 1_700_000_000_000  # FakeRiot sets game_start = this + the match number

async def seed(client, fake_riot):
    fake_riot.match_ids = ["M1", "M2", "M3"]
    await client.get("/api/players/Faker/KR1/matches")

def m(match_id, champion, win, k, d, a, cs, minutes, start_offset_ms):
    return MatchSummary(
        match_id=match_id, champion=champion, win=win,
        kills=k, deaths=d, assists=a, cs=cs,
        duration_seconds=minutes * 60, game_start=BASE + start_offset_ms,
    )


# Newest first, like the DB returns them. compute_stats must sort them itself.
MATCHES = [
    m("D", "Ahri", True, 3, 3, 3, 120, 20, 7_200_000),   # 00:13 UTC
    m("C", "Zed",  True, 10, 0, 2, 210, 30, 3_600_000),  # 23:13 UTC
    m("B", "Ahri", False, 2, 4, 2, 150, 30, 2_400_000),  # 22:53 UTC
    m("A", "Ahri", True, 5, 1, 5, 180, 30, 0),           # 22:13 UTC
]


def test_summary():
    s = compute_stats(MATCHES)["summary"]
    assert s["games"] == 4
    assert s["wins"] == 3
    assert s["win_rate"] == pytest.approx(0.75)
    assert s["kda"] == pytest.approx(4.0)         # (20 kills + 12 assists) / 8 deaths
    assert s["avg_kills"] == pytest.approx(5.0)
    assert s["avg_deaths"] == pytest.approx(2.0)
    assert s["avg_assists"] == pytest.approx(3.0)
    assert s["cs_per_min"] == pytest.approx(6.0)  # 660 CS / 110 minutes


def test_champions_sorted_by_games():
    champs = compute_stats(MATCHES)["champions"]
    assert [c["champion"] for c in champs] == ["Ahri", "Zed"]
    assert champs[0]["games"] == 3
    assert champs[0]["win_rate"] == pytest.approx(2 / 3)
    assert champs[0]["kda"] == pytest.approx(2.5)   # (10 + 10) / 8
    assert champs[1]["kda"] == pytest.approx(12.0)  # 0 deaths counts as 1


def test_trend_is_oldest_first_with_rolling_average():
    trend = compute_stats(MATCHES)["kda_trend"]
    assert [t["match_id"] for t in trend] == ["A", "B", "C", "D"]
    assert [t["kda"] for t in trend] == pytest.approx([10.0, 1.0, 12.0, 2.0])
    assert trend[1]["kda_rolling"] == pytest.approx(5.5)
    assert trend[3]["kda_rolling"] == pytest.approx(6.25)


def test_by_hour_utc():
    by_hour = compute_stats(MATCHES, tz="UTC")["by_hour"]
    assert [(h["hour"], h["games"], h["wins"]) for h in by_hour] == [
        (0, 1, 1), (22, 2, 1), (23, 1, 1),
    ]


def test_by_hour_respects_timezone():
    by_hour = compute_stats(MATCHES, tz="Asia/Tokyo")["by_hour"]  # UTC+9, no DST
    assert [h["hour"] for h in by_hour] == [7, 8, 9]


def test_empty_input():
    result = compute_stats([])
    assert result["summary"]["games"] == 0
    assert result["champions"] == []


# --- endpoint tests, reusing the fixtures from conftest.py ---

async def test_stats_endpoint(client, fake_riot):
    fake_riot.match_ids = ["M1", "M2", "M3"]
    await client.get("/api/players/Faker/KR1/matches")  # populate the DB

    r = await client.get("/api/players/faker/kr1/stats")  # lowercase on purpose
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["games"] == 3
    assert body["summary"]["win_rate"] == 1.0
    # FakeRiot gives kills = 1, 2, 3, deaths = 1, assists = 2 per match
    assert body["summary"]["kda"] == pytest.approx(4.0)  # (6 + 6) / 3


async def test_stats_unknown_player_returns_404(client):
    r = await client.get("/api/players/Nobody/EUW/stats")
    assert r.status_code == 404


async def test_stats_bad_timezone_returns_422(client):
    r = await client.get("/api/players/Faker/KR1/stats?tz=Not/AZone")
    assert r.status_code == 422

async def test_stats_filter_by_champion(client, fake_riot):
    await seed(client, fake_riot)

    r = await client.get(STATS, params={"champion": "ahri"})  # FakeRiot plays Ahri
    assert r.json()["summary"]["games"] == 3

    r = await client.get(STATS, params={"champion": "Zed"})
    assert r.status_code == 200
    assert r.json()["summary"]["games"] == 0

async def test_stats_filter_by_date_range(client, fake_riot):
    await seed(client, fake_riot)

    r = await client.get(STATS, params={"start": BASE_MS + 2})
    assert r.json()["summary"]["games"] == 2  # M2, M3

    r = await client.get(STATS, params={"start": BASE_MS + 1, "end": BASE_MS + 2})
    assert r.json()["summary"]["games"] == 2  # M1, M2


async def test_stats_rejects_inverted_range(client):
    r = await client.get(STATS, params={"start": 10, "end": 5})
    assert r.status_code == 422