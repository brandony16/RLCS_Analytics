import argparse
import pandas as pd
from src.features.scoreboard import get_detailed_scoreboard, print_scoreboard


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
    # df_physics = pd.read_csv(frames_path)
    # final_report = merge_physics_with_scoreboard(scoreboard_df, df_physics)


if __name__ == "__main__":
    main()
