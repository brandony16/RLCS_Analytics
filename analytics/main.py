import argparse
import pandas as pd
from features.scoreboard import get_detailed_scoreboard, print_scoreboard
from features.aggregation import (
    generate_frame_stats,
    print_frame_stats,
    show_boost_by_player_graph,
)
from typing import Dict, List, Any
import json


def main():
    parser = argparse.ArgumentParser(description="Rocket League Analytics Pipeline")

    # Allows you to specify the match ID via command line
    parser.add_argument("match_guid", help="The GUID of the match to analyze")
    parser.add_argument(
        "--data_dir", default="data/processed", help="Directory where files are stored"
    )

    args = parser.parse_args()

    metadata_path = f"{args.data_dir}/{args.match_guid}_metadata.json"
    frames_path = f"{args.data_dir}/{args.match_guid}_frames.csv"

    print(f"--- Analyzing Match: {args.match_guid} ---")

    # 1. Get Scoreboard
    scoreboard_df = get_detailed_scoreboard(metadata_path)
    print("\nOfficial Scoreboard:")
    print_scoreboard(scoreboard_df)

    # 2. Add Physics Stats (To be implemented)
    with open(metadata_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    goals = data.get("properties", {}).get("Goals", [])

    df_frames = pd.read_csv(frames_path)
    calcuated_stats = generate_frame_stats(df_frames)
    print_frame_stats(calcuated_stats)

    show_boost_by_player_graph(df_frames, goals)


if __name__ == "__main__":
    main()
