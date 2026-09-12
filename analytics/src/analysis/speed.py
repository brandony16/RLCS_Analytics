import numpy as np
import pandas as pd
import constants as C


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