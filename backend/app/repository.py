from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Match, Player
from .schemas import MatchSummary


async def upsert_player(session: AsyncSession, puuid: str, game_name: str, tag_line: str):
    player = await session.get(Player, puuid)
    if player is None:
        session.add(Player(puuid=puuid, game_name=game_name, tag_line=tag_line))
    else:
        # Riot IDs can be renamed, keep ours current
        player.game_name, player.tag_line = game_name, tag_line
    await session.commit()


async def get_stored_match_ids(session: AsyncSession, puuid: str, match_ids: list[str]) -> set[str]:
    if not match_ids:
        return set()
    result = await session.scalars(
        select(Match.match_id).where(Match.puuid == puuid, Match.match_id.in_(match_ids))
    )
    return set(result)


async def save_matches(session: AsyncSession, puuid: str, summaries: list[MatchSummary]):
    session.add_all(Match(puuid=puuid, **s.model_dump()) for s in summaries)
    await session.commit()


async def get_matches(session: AsyncSession, puuid: str, match_ids: list[str]) -> list[Match]:
    result = await session.scalars(
        select(Match)
        .where(Match.puuid == puuid, Match.match_id.in_(match_ids))
        .order_by(Match.game_start.desc())
    )
    return list(result)

async def get_player_by_riot_id(session: AsyncSession, game_name: str, tag_line: str) -> Player | None:
    # Riot IDs are case-insensitive, but SQLite's == on text is case-sensitive
    return await session.scalar(
        select(Player).where(
            func.lower(Player.game_name) == game_name.lower(),
            func.lower(Player.tag_line) == tag_line.lower(),
        )
    )

async def get_recent_matches(
    session: AsyncSession,
    puuid: str,
    limit: int,
    champion: str | None = None,
    start: int | None = None,
    end: int | None = None,
) -> list[Match]:
    stmt = select(Match).where(Match.puuid == puuid)
    if champion:
        stmt = stmt.where(func.lower(Match.champion) == champion.lower())
    if start is not None:
        stmt = stmt.where(Match.game_start >= start)
    if end is not None:
        stmt = stmt.where(Match.game_start <= end)
    stmt = stmt.order_by(Match.game_start.desc()).limit(limit)

    result = await session.scalars(stmt)
    return list(result)