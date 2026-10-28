import asyncio
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pathlib import Path

from . import repository
from .db import Base, engine, get_session
from .riot_client import RiotClient, RiotError
from .schemas import MatchSummary, PlayerMatches, PlayerStats
from .stats import compute_stats
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.http = httpx.AsyncClient(timeout=10)
    yield
    await app.state.http.aclose()

app = FastAPI(title="LoL Match Analyzer", lifespan=lifespan)


def get_riot(request: Request) -> RiotClient:
    return RiotClient(request.app.state.http)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/players/{game_name}/{tag_line}/matches", response_model=PlayerMatches)
async def player_matches(
    game_name: str,
    tag_line: str,
    count: int = Query(10, ge=1, le=20),
    riot: RiotClient = Depends(get_riot),
    session: AsyncSession = Depends(get_session),
):
    try:
        
        puuid = await riot.get_puuid(game_name, tag_line)
        await repository.upsert_player(session, puuid, game_name, tag_line)

        match_ids = await riot.get_match_ids(puuid, count)
        stored = await repository.get_stored_match_ids(session, puuid, match_ids)
        missing = [mid for mid in match_ids if mid not in stored]

        if missing:
            fetched = await asyncio.gather(
                *(riot.get_match_summary(mid, puuid) for mid in missing)
            )
            await repository.save_matches(session, puuid, list(fetched))
    except RiotError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    rows = await repository.get_matches(session, puuid, match_ids)
    return PlayerMatches(
        game_name=game_name,
        tag_line=tag_line,
        matches=[MatchSummary.model_validate(r) for r in rows],
    )

@app.get("/api/players/{game_name}/{tag_line}/stats", response_model=PlayerStats)
async def player_stats(
    game_name: str,
    tag_line: str,
    limit: int = Query(50, ge=1, le=500),
    tz: str = Query("UTC", description="IANA timezone, e.g. Asia/Tokyo"),
    champion: str | None = Query(None, description="Champion name, case-insensitive"),
    start: int | None = Query(None, description="Earliest game start, epoch ms"),
    end: int | None = Query(None, description="Latest game start, epoch ms"),
    session: AsyncSession = Depends(get_session),
):
    if start is not None and end is not None and start > end:
        raise HTTPException(status_code=422, detail="start must be <= end")

    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(status_code=422, detail=f"Unknown timezone: {tz}")

    player = await repository.get_player_by_riot_id(session, game_name, tag_line)
    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found. Fetch their matches first.",
        )

    rows = await repository.get_recent_matches(
        session, player.puuid, limit, champion, start, end
    )
    matches = [MatchSummary.model_validate(r) for r in rows]
    return PlayerStats(game_name=game_name, tag_line=tag_line, **compute_stats(matches, tz))

# --- Serve the built React app (only exists inside the Docker image) ---
STATIC_DIR = (Path(__file__).resolve().parent.parent / "static")

if STATIC_DIR.is_dir():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (STATIC_DIR / full_path).resolve()
        # Serve a real file if it exists (and stays inside static/), else the SPA entry point
        if candidate.is_file() and STATIC_DIR in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")