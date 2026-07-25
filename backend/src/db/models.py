from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.database import Base


class Match(Base):
    __tablename__ = "matches"

    # MatchGUID is a string like "12345678-abcd-..." and serves as our primary key
    match_guid: Mapped[str] = mapped_column(String(50), primary_key=True)
    map_name: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship: Gives us `match.players` -> list of PlayerScoreboard objects
    players: Mapped[List["PlayerScoreboard"]] = relationship(
        "PlayerScoreboard", back_populates="match", cascade="all, delete-orphan"
    )


class PlayerScoreboard(Base):
    __tablename__ = "player_scoreboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key linking this record back to a specific match
    match_id: Mapped[str] = mapped_column(String(50), ForeignKey("matches.match_guid"))

    # Static Box Score Stats
    player_name: Mapped[str] = mapped_column(String(100))
    team: Mapped[int] = mapped_column(Integer)  # 0 for Blue, 1 for Orange
    score: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    shots: Mapped[int] = mapped_column(Integer, default=0)
    demos: Mapped[int] = mapped_column(Integer, default=0)

    # Link back to parent Match object
    match: Mapped["Match"] = relationship("Match", back_populates="players")
