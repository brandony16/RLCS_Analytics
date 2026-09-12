import pandas as pd
import numpy as np
from typing import Any, Dict, Iterable, Optional


def _reset_frames(events: Optional[Iterable[Dict[str, Any]]]) -> np.ndarray:
    if not events:
        return np.array([], dtype=float)

    frames = [
        event.get("frame")
        for event in events
        if event.get("type") == "reset" and event.get("frame") is not None
    ]
    return np.array(sorted(set(frames)), dtype=float)


def calculate_boost_usage(
    df: pd.DataFrame,
    events: Optional[Iterable[Dict[str, Any]]] = None,
    max_boost_drop: float = 40.0,
) -> pd.DataFrame:
    """
    Calculates the amount of boost spent frame-to-frame, filtering out
    impossible drops caused by lag or demo respawns
    Adds columns named boost_used and boost_diff
    """
    df_out = df.copy()
    reset_frames = _reset_frames(events)

    # Work in player/frame order so reset boundaries are detected even when
    # a player has no row on the exact reset frame.
    ordered = df_out.sort_values(["player_name", "frame"]).copy()
    ordered["previous_boost"] = ordered.groupby("player_name")["boost_amount"].shift()
    ordered["previous_frame"] = ordered.groupby("player_name")["frame"].shift()

    if len(reset_frames):
        current_reset_count = np.searchsorted(
            reset_frames, ordered["frame"].to_numpy(), side="right"
        )
        previous_reset_count = np.searchsorted(
            reset_frames,
            ordered["previous_frame"].fillna(-1).to_numpy(),
            side="right",
        )
        crossed_reset = current_reset_count > previous_reset_count
    else:
        crossed_reset = np.zeros(len(ordered), dtype=bool)

    ordered["is_reset_boundary"] = crossed_reset
    ordered["boost_diff"] = ordered["boost_amount"] - ordered["previous_boost"]
    is_valid_usage = (
        (ordered["boost_diff"] < 0)
        & (ordered["boost_diff"] >= -max_boost_drop)
        & ~ordered["is_reset_boundary"]
    )
    ordered["boost_used"] = np.where(
        is_valid_usage, ordered["boost_diff"].abs(), 0.0
    )

    return ordered.drop(columns=["previous_boost", "previous_frame"]).sort_index()
