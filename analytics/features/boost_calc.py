import pandas as pd
import numpy as np


def calculate_boost_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the amount of boost spent frame-to-frame, filtering out
    impossible drops caused by lag or demo respawns
    Adds columns named boost_used and boost_diff
    """
    df_out = df.copy()

    # Calculate the frame-to-frame difference for each player
    df_out["boost_diff"] = df_out.groupby("player_name")["boost_amount"].diff()

    is_valid_usage = (df_out["boost_diff"] < 0) & (df_out["boost_diff"] >= -40.0)

    # Extract only the valid spent amounts
    df_out["boost_used"] = np.where(is_valid_usage, abs(df_out["boost_diff"]), 0.0)

    return df_out
