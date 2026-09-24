import numpy as np
import pandas as pd
from pandas import DataFrame

from constants import MAX_TOUCH_DIST, MIN_IMPULSE
from src.domain.models import FrameTable, TouchTable


def get_touch_df(
    df: DataFrame,
    max_touch_dist: float = MAX_TOUCH_DIST,
    min_impulse: float = MIN_IMPULSE,
    impulse_window: int = 2,
    cluster_gap: int = 6,
) -> TouchTable:
    """
    Estimate discrete player-ball touches from frame-level replay data.

    Ball velocity and car position are replication streams, so the strongest
    evidence for a touch may arrive a few frames before or after the closest
    player-ball sample. This function uses a short impulse window, then emits
    one representative row per player contact episode.
    """

    ball_mask = df["player_name"] == "Ball"
    ball_df = df[ball_mask].copy()
    car_df = df[~ball_mask].copy()

    if ball_df.empty or car_df.empty:
        return TouchTable(pd.DataFrame())

    merged = get_player_distance_to_ball_df(df, impulse_window=impulse_window)

    candidates = merged[
        (merged["dist_to_ball"] <= max_touch_dist)
        & (merged["impact_frame"] >= merged["frame"])
        & (
            (merged["impulse_window"] >= min_impulse)
            | (
                (merged["frame"] <= 300)
                & (merged["ball_speed"] >= 1000)
                & (merged["dist_to_ball"] <= max_touch_dist)
            )
        )
    ].copy()

    if candidates.empty:
        return TouchTable(pd.DataFrame())

    # For a 50/50, only the closest player owns the frame-level candidate.
    candidates = (
        candidates.sort_values(["frame", "dist_to_ball"])
        .groupby("frame", as_index=False)
        .first()
    )

    # Consecutive candidate frames usually represent one replicated contact.
    candidates = candidates.sort_values(["player_name", "frame"]).reset_index(drop=True)
    player_changed = candidates["player_name"].ne(candidates["player_name"].shift())
    frame_gap = candidates.groupby("player_name")["frame"].diff().gt(cluster_gap)
    candidates["possession_cluster_id"] = (player_changed | frame_gap).cumsum()

    # Keep the strongest evidence from each contact episode, not every nearby
    # frame. The returned frame is the best estimate of the touch moment.
    candidates = candidates.sort_values(
        ["possession_cluster_id", "impact_impulse", "dist_to_ball"],
        ascending=[True, False, True],
    )
    candidates = (
        candidates.groupby("possession_cluster_id", as_index=False)
        .first()
        .sort_values("frame")
        .reset_index(drop=True)
    )

    return TouchTable(candidates)


def get_player_distance_to_ball_df(
    df: DataFrame, impulse_window: int = 2
) -> FrameTable:
    """Return player-ball distances with ball motion context for debugging."""
    ball_mask = df["player_name"] == "Ball"
    ball_df = df[ball_mask].copy()
    car_df = df[~ball_mask].copy()

    if ball_df.empty or car_df.empty:
        return pd.DataFrame()

    min_frame, max_frame = df["frame"].min(), df["frame"].max()
    processed_ball = _process_ball_df(
        ball_df, min_frame, max_frame, impulse_window
    )
    merged = _add_distance_to_ball(
        car_df.merge(processed_ball.reset_index(), on="frame", how="inner")
    )
    return FrameTable(merged)


def _add_distance_to_ball(merged: DataFrame) -> DataFrame:
    result = merged.copy()
    position_delta = (
        result[["loc_x", "loc_y", "loc_z"]].to_numpy()
        - result[["ball_x", "ball_y", "ball_z"]].to_numpy()
    )
    result["dist_to_ball"] = np.linalg.norm(position_delta, axis=1)
    return result


def _process_ball_df(
    ball_df: DataFrame, min_frame: int, max_frame: int, impulse_window: int = 2
) -> DataFrame:
    full_frame_idx = pd.Index(np.arange(min_frame, max_frame + 1), name="frame")

    ball_cols = [
        "frame",
        "time",
        "loc_x",
        "loc_y",
        "loc_z",
        "lin_vel_x",
        "lin_vel_y",
        "lin_vel_z",
    ]
    ball = ball_df[ball_cols].drop_duplicates("frame").set_index("frame")
    ball = ball.reindex(full_frame_idx)

    # Forward-fill position and time because the network stream is delta encoded.
    pos_cols = ["loc_x", "loc_y", "loc_z", "time"]
    ball[pos_cols] = ball[pos_cols].ffill()

    # Hold the last known velocity instead of turning missing updates into a
    # false stop/start impulse.
    vel_cols = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    ball[vel_cols] = ball[vel_cols].ffill().bfill().fillna(0.0)

    # Compute velocity change and allow for replication skew around contact.
    velocity_delta = ball[vel_cols].diff()
    ball["ball_impulse"] = np.sqrt((velocity_delta**2).sum(axis=1)).fillna(0.0)
    ball["ball_speed"] = np.sqrt((ball[vel_cols] ** 2).sum(axis=1))
    window_size = max(1, 2 * impulse_window + 1)
    ball["impulse_window"] = (
        ball["ball_impulse"].rolling(window_size, center=True, min_periods=1).max()
    )
    impulse_values = ball["ball_impulse"].to_numpy()
    frame_values = ball.index.to_numpy()
    impact_frames = []
    for position in range(len(ball)):
        start = max(0, position - impulse_window)
        end = min(len(ball), position + impulse_window + 1)
        impact_frames.append(frame_values[start + np.argmax(impulse_values[start:end])])
    ball["impact_frame"] = impact_frames
    ball["impact_impulse"] = ball["impulse_window"]

    return ball.rename(
        columns={
            "loc_x": "ball_x",
            "loc_y": "ball_y",
            "loc_z": "ball_z",
            "lin_vel_x": "ball_vx",
            "lin_vel_y": "ball_vy",
            "lin_vel_z": "ball_vz",
            "time": "ball_time",
        }
    )
