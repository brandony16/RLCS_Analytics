import pandas as pd
import numpy as np


def calculate_boost_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the amount of boost spent frame-to-frame, filtering out
    impossible drops caused by lag or demo respawns
    """
    df_out = df.copy()

    # Calculate the frame-to-frame difference for each player
    df_out["boost_diff"] = df_out.groupby("player_name")["boost_amount"].diff()

    # Max consumption 33.3/s, which is ~1.11 per frame. We use -10.0 as a safe boundary
    # to account for minor network packet grouping while catching demos.
    is_valid_usage = (df_out["boost_diff"] < 0) & (df_out["boost_diff"] >= -10.0)

    # Extract only the valid spent amounts
    df_out["boost_used"] = np.where(is_valid_usage, abs(df_out["boost_diff"]), 0.0)

    return df_out
