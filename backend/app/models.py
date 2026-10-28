from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Player(Base):
    __tablename__ = "players"

    puuid: Mapped[str] = mapped_column(String, primary_key=True)
    game_name: Mapped[str] = mapped_column(String)
    tag_line: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("game_name", "tag_line"),)


class Match(Base):
    __tablename__ = "matches"

    # One row per (match, player). A match_id alone isn't unique here
    # because later you may store several players from the same game.
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str] = mapped_column(String, index=True)
    puuid: Mapped[str] = mapped_column(ForeignKey("players.puuid"), index=True)
    champion: Mapped[str] = mapped_column(String)
    win: Mapped[bool] = mapped_column(Boolean)
    kills: Mapped[int] = mapped_column(Integer)
    deaths: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    cs: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    game_start: Mapped[int] = mapped_column(BigInteger)  # epoch ms, used for "play after 11pm" later

    __table_args__ = (UniqueConstraint("match_id", "puuid"),)