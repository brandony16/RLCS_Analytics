from pandas import DataFrame
from src.analysis.boost import calculate_boost_usage
from src.analysis.speed import calculate_speeds

def generate_frame_stats(df: DataFrame, events=None):
    """
    Generates basic stats from the frame-by-frame dataframe.
    These stats include:
    - Avg. Speed (km/h)
    - Boost Usage
    """
    modified_df = df.copy()

    # adds boost_used, speed_uu, and speed_kmh columns
    modified_df = calculate_boost_usage(modified_df, events=events)
    modified_df = calculate_speeds(modified_df)

    modified_df = modified_df[modified_df["player_name"] != "Ball"]

    df_out = modified_df.groupby("player_name").agg(
        boost_usage=("boost_used", "sum"),
        avg_speed_kmh=("speed_kmh", "mean"),
        avg_speed_uu=("speed_uu", "mean"),
    )

    return df_out.round(2)