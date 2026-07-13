import pandas as pd


def aggregate_player_stats(df: pd.DataFrame):
    """
    Groups the frame-by-frame dataset by player to generate summary statistics.
    """
    stats = (
        df.groupby("player_name")
        .agg(
            avg_speed_kmh=("speed_kmh", "mean"),
            max_speed_kmh=("speed_kmh", "max"),
            total_boost_used=("boost_used", "sum"),
        )
        .reset_index()
    )

    return stats.round(2)
