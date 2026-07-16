import json
import pandas as pd
from typing import Dict, List, Any
from backend.src.constants import ORANGE_TEAM, BLUE_TEAM


def flatten_player_stats(
    raw_stats: List[Dict[str, Any]], demos_dict: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Extracts relevant fields from the nested rrrocket PlayerStats structure
    and merges the calculated demo counts.
    """
    flattened = []
    for player in raw_stats:
        player_name = player.get("Name")
        # Fetch the demo count from our dict, defaulting to 0 if they got no demos
        player_demos = (
            demos_dict.get(player_name) if (demos_dict and player_name) else 0
        )

        flattened.append(
            {
                "player_name": player_name,
                "team": player.get("Team"),
                "score": player.get("Score", 0),
                "goals": player.get("Goals", 0),
                "assists": player.get("Assists", 0),
                "saves": player.get("Saves", 0),
                "shots": player.get("Shots", 0),
                "demos": player_demos or 0,  # New Column!
            }
        )
    return flattened


def get_detailed_scoreboard(metadata_json_path: str) -> pd.DataFrame:
    """
    Parses the metadata JSON and returns the official scoreboard as a DataFrame.
    """
    with open(metadata_json_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # Extract the nested PlayerStats list and the demos dictionary
    raw_stats = data.get("properties", {}).get("PlayerStats", [])
    demos = data.get("demos", {})  # Defaults to an empty dict if missing

    # Flatten the data structure and inject the demos
    clean_stats = flatten_player_stats(raw_stats, demos)

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
    print(blue_players.drop(columns=["team"]).to_string(index=False))

    print("== ORANGE " + "=" * 50)
    orange_players = orange_players.sort_values(by="score", ascending=False)
    print(orange_players.drop(columns=["team"]).to_string(index=False))

    print("=" * 60 + "\n")
