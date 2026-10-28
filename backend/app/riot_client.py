import asyncio
import httpx

from .config import settings
from .schemas import MatchSummary


class RiotError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class RiotClient:
    # Shared across instances: limits concurrent in-flight requests to Riot
    _semaphore = asyncio.Semaphore(5)
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._headers = {"X-Riot-Token": settings.riot_api_key}

    async def _get(self, url: str, params: dict | None = None, retries: int = 3):
        for attempt in range(retries + 1):
            async with self._semaphore:
                resp = await self._client.get(url, headers=self._headers, params=params)

            if resp.status_code == 429 and attempt < retries:
                # Riot tells us how long to wait
                wait = int(resp.headers.get("Retry-After", 2))
                await asyncio.sleep(wait)
                continue
            break

        if resp.status_code == 404:
            raise RiotError(404, "Not found")
        if resp.status_code == 429:
            raise RiotError(429, "Rate limited by Riot, try again shortly")
        if resp.status_code in (401, 403):
            raise RiotError(502, "Riot API key invalid or expired")
        resp.raise_for_status()
        return resp.json()

    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        url = (
            f"https://{settings.riot_regional_host}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        data = await self._get(url)
        return data["puuid"]

    async def get_match_ids(self, puuid: str, count: int = 20) -> list[str]:
        url = (
            f"https://{settings.riot_match_host}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )
        return await self._get(url, params={"count": count, "queue": 420})  # 420 = ranked solo

    async def get_match_summary(self, match_id: str, puuid: str) -> MatchSummary:
        # Add this temporary print statement:
        print(f"[DEBUG] get_match_summary called for ID: {match_id}")
        
        url = (
            f"https://{settings.riot_match_host}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}"
        )
        data = await self._get(url)
        info = data["info"]
        me = next(p for p in info["participants"] if p["puuid"] == puuid)
        return MatchSummary(
            match_id=match_id,
            champion=me["championName"],
            win=me["win"],
            kills=me["kills"],
            deaths=me["deaths"],
            assists=me["assists"],
            cs=me["totalMinionsKilled"] + me["neutralMinionsKilled"],
            duration_seconds=info["gameDuration"],
            game_start=info["gameStartTimestamp"],
        )