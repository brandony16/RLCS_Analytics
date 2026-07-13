import numpy as np
import pandas as pd
from src import constants as C


def calculate_speeds(df: pd.DataFrame):
    """
    Calculates the magnitude of the 3D velocity vector in Unreal Units (uu/s)
    and converts it to kilometers per hour (km/h).
    """
    df_out = df.copy()

    df_out["speed_uu"] = np.sqrt(
        df_out["lin_vel_x"] ** 2 + df_out["lin_vel_y"] ** 2 + df_out["lin_vel_z"] ** 2
    )

    # 1 uu/s = 0.036 km/h
    df_out["speed_kmh"] = df_out["speed_uu"] * 0.036

    return df_out


def filter_impossible_speeds(
    df: pd.DataFrame, max_uu_speed: float = (C.UU_CAR_MAX_SPEED + 100)
):
    """
    Drops frames where the calculated speed exceeds the physical limits of the game.
    The theoretical max is 2300 uu/s, 100 offset allows for some wiggle room
    while filtering out lag corrections and demo respawns.
    """
    return df[df["speed_uu"] <= max_uu_speed].copy()
