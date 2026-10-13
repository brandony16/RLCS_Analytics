import numpy as np
import pandas as pd
import constants as C

from src.domain.models import FrameAnalysisTable


def calculate_speeds(df: pd.DataFrame) -> FrameAnalysisTable:
    """
    Calculates the magnitude of the 3D velocity vector in Unreal Units (uu/s)
    and converts it to kilometers per hour (km/h).
    """
    df_in = df.to_df() if hasattr(df, "to_df") else df.copy()
    df_out = df_in.copy()

    df_out["speed_uu"] = np.sqrt(
        df_out["lin_vel_x"] ** 2 + df_out["lin_vel_y"] ** 2 + df_out["lin_vel_z"] ** 2
    )

    # 1 uu/s = 0.036 km/h
    df_out["speed_kmh"] = df_out["speed_uu"] * 0.036

    return FrameAnalysisTable(df_out)