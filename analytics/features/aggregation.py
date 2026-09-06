from pandas import DataFrame
from features.boost_calc import calculate_boost_usage
from features.physics_calc import calculate_speeds, filter_impossible_speeds
import matplotlib.pyplot as plt
from typing import List, Dict, Any

def generate_frame_stats(df: DataFrame):
    """
    Generates basic stats from the frame-by-frame dataframe.
    These stats include:
    - Avg. Speed (km/h)
    - Boost Usage
    """
    modified_df = df.copy()

    # adds boost_used, speed_uu, and speed_kmh columns
    modified_df = calculate_boost_usage(modified_df)
    modified_df = calculate_speeds(modified_df)

    modified_df = modified_df[modified_df["player_name"] != "Ball"]

    df_out = modified_df.groupby("player_name").agg(
        boost_usage=("boost_used", "sum"),
        avg_speed_kmh=("speed_kmh", "mean"),
        avg_speed_uu=("speed_uu", "mean"),
    )

    return df_out.round(2)


def print_frame_stats(df: DataFrame):
    """
    Prints out the calculated stats from generate_frame_stats in a formatted
    and readable way.
    """
    print("== BOOST AND SPEED STATS " + "=" * 52)
    print(df.to_string(index=True))
    print("=" * 60 + "\n")

def show_boost_by_player_graph(df: DataFrame, goals: List[Dict[str, Any]]):  
  for player, player_df in df.groupby("player_name"):
    if player == "zen":
      plt.plot(player_df["game_time"], player_df["boost_amount"], label=player, marker="o")

  plt.axhline(y=33.33, color='red', linestyle=':')


  for goal_event in goals:
    frame = df[df["frame"] == goal_event.get("frame")]
    time = frame.iloc[0]["game_time"]
    plt.axvline(x=time, color="green", linestyle=":")

  plt.xlabel("Time")
  plt.ylabel("Boost")
  plt.title("Boost Over Time")
  plt.legend()
  plt.show()