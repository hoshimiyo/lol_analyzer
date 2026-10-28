from fastapi.testclient import TestClient

from app.main import app, get_riot
from app.riot_client import RiotError
from app.schemas import MatchSummary


class FakeRiot:
    """Stands in for RiotClient. Same method names, no network."""

    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        return "fake-puuid"

    async def get_match_ids(self, puuid: str, count: int = 20) -> list[str]:
        return ["VN2_1", "VN2_2"][:count]

    async def get_match_summary(self, match_id: str, puuid: str) -> MatchSummary:
        return MatchSummary(
            match_id=match_id,
            champion="Ahri",
            win=True,
            kills=7,
            deaths=2,
            assists=9,
            cs=215,
            duration_seconds=1830,
            game_start=1752169182421
        )


class NotFoundRiot(FakeRiot):
    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        raise RiotError(404, "Not found")


def make_client(fake) -> TestClient:
    app.dependency_overrides[get_riot] = lambda: fake
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


async def test_player_matches_response_shape(client, fake_riot):
    fake_riot.match_ids = ["M1"]

    r = await client.get("/api/players/Faker/KR1/matches")

    assert r.status_code == 200
    body = r.json()
    assert body["game_name"] == "Faker"
    assert body["tag_line"] == "KR1"
    assert set(body["matches"][0]) == {
        "match_id", "champion", "win", "kills", "deaths",
        "assists", "cs", "duration_seconds", "game_start",
    }


def test_unknown_player_returns_404():
    client = make_client(NotFoundRiot())

    resp = client.get("/api/players/Nobody/0000/matches")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Not found"

URL = "/api/players/Faker/KR1/matches"


async def test_second_call_only_fetches_new_matches(client, fake_riot):
    # First call: nothing stored yet, so all three matches are fetched
    fake_riot.match_ids = ["M1", "M2", "M3"]
    r1 = await client.get(URL)

    assert r1.status_code == 200
    assert sorted(fake_riot.summary_calls) == ["M1", "M2", "M3"]

    # Second call: M4 is new, M1 and M2 are already stored
    fake_riot.summary_calls.clear()
    fake_riot.match_ids = ["M4", "M1", "M2"]
    r2 = await client.get(URL)

    assert r2.status_code == 200
    assert fake_riot.summary_calls == ["M4"]

    # Response comes from the DB, newest first
    assert [m["match_id"] for m in r2.json()["matches"]] == ["M4", "M2", "M1"]


async def test_repeat_call_makes_no_match_requests(client, fake_riot):
    fake_riot.match_ids = ["M1", "M2"]
    await client.get(URL)

    fake_riot.summary_calls.clear()
    r = await client.get(URL)

    assert r.status_code == 200
    assert fake_riot.summary_calls == []
    assert len(r.json()["matches"]) == 2