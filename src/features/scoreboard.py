import json
import pandas as pd
from typing import Dict, List, Any
from src.constants import ORANGE_TEAM, BLUE_TEAM


def flatten_player_stats(raw_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts relevant fields from the nested rrrocket PlayerStats structure.
    """
    flattened = []
    for player in raw_stats:
        flattened.append(
            {
                "player_name": player.get("Name"),
                "team": player.get("Team"),
                "score": player.get("Score", 0),
                "goals": player.get("Goals", 0),
                "assists": player.get("Assists", 0),
                "saves": player.get("Saves", 0),
                "shots": player.get("Shots", 0),
            }
        )
    return flattened


def get_detailed_scoreboard(metadata_json_path: str) -> pd.DataFrame:
    """
    Parses the metadata JSON and returns the official scoreboard as a DataFrame.
    """
    with open(metadata_json_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # Extract the nested PlayerStats list
    raw_stats = data.get("properties", {}).get("PlayerStats", [])

    # Flatten the data structure
    clean_stats = flatten_player_stats(raw_stats)

    # Convert to DataFrame and sort by score
    df = pd.DataFrame(clean_stats)

    if not df.empty:
        df = df.sort_values(by="score", ascending=False).reset_index(drop=True)

    return df


def print_scoreboard(scoreboard_df: pd.DataFrame):
    """
    Prints out the scoreboard result from get_detailed_scoreboard in a formatted
    and more readable way.
    """
    blue_players = scoreboard_df[scoreboard_df["team"] == BLUE_TEAM]
    orange_players = scoreboard_df[scoreboard_df["team"] == ORANGE_TEAM]

    print("== BLUE " + "=" * 52)
    blue_players = blue_players.sort_values(by="score", ascending=False)
    print(blue_players.drop(columns=["team"]).to_string())

    print("== ORANGE " + "=" * 50)
    orange_players = orange_players.sort_values(by="score", ascending=False)
    print(orange_players.drop(columns=["team"]).to_string())

    print("=" * 60 + "\n")
