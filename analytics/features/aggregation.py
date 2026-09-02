from pandas import DataFrame
from features.boost_calc import calculate_boost_usage
from features.physics_calc import calculate_speeds, filter_impossible_speeds
import matplotlib.pyplot as plt

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

def show_boost_by_player_graph(df: DataFrame):  
  for player, player_df in df.groupby("player_name"):
    plt.plot(player_df["time"], player_df["boost_amount"], label=player)

  plt.xlabel("Time")
  plt.ylabel("Boost")
  plt.title("Boost Over Time")
  plt.legend()
  plt.show()