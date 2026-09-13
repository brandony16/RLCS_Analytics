import argparse
import json
from typing import Any, Dict

import pandas as pd

from src.analysis.aggregation import generate_frame_stats
from src.analysis.scoreboard import get_detailed_scoreboard, print_scoreboard
from src.visualization.charts import show_speed_by_player_graph
from src.visualization.heatmaps import show_player_position_heatmaps
from src.visualization.terminal import print_frame_stats


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
    events = data.get("events", [])

    df_frames = pd.read_csv(frames_path)
    calculated_stats = generate_frame_stats(df_frames, events=events)
    print_frame_stats(calculated_stats)

    show_player_position_heatmaps(["zen", "Atow", "vatira"], df_frames)
    # show_speed_by_player_graph(df_frames, events, ["Atow"])
    # show_boost_by_player_graph(df_frames, events, ["Atow", "zen"])


if __name__ == "__main__":
    main()
