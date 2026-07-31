# backend/src/core/services.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.db.models import Match, PlayerScoreboard


def save_match_to_db(
    db: Session,
    match_guid: str,
    map_name: str,
    flattened_stats: List[Dict[str, Any]],
) -> Match:
    """
    Saves a parsed match and its player scoreboards to PostgreSQL.
    If the match already exists, returns the existing record.
    """
    # Check for existing match
    existing_match = db.query(Match).filter(Match.match_guid == match_guid).first()
    if existing_match:
        return existing_match

    new_match = Match(
        match_guid=match_guid,
        map_name=map_name,
    )

    # Create PlayerScoreboard objects
    for player in flattened_stats:
        player_score = PlayerScoreboard(
            player_name=player.get("player_name", "Unknown"),
            team=player.get("team", 0),
            score=player.get("score", 0),
            goals=player.get("goals", 0),
            assists=player.get("assists", 0),
            saves=player.get("saves", 0),
            shots=player.get("shots", 0),
            demos=player.get("demos", 0),
        )
        new_match.players.append(player_score)

    # 4. Commit to database
    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    return new_match
