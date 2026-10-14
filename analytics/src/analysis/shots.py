import pandas as pd
from pandas import DataFrame
import constants as C
import numpy as np

from src.domain.models import ShotTable, TouchTable, FrameTable


def get_shots(
    touch_df: TouchTable | DataFrame, name_to_team: dict, frame_df: FrameTable
) -> ShotTable:
    shots = []
    df = touch_df.df if isinstance(touch_df, TouchTable) else touch_df

    max_z = C.GOAL_HEIGHT + (C.BALL_RADIUS * 2)  # height of goal plus 1 ball
    min_x = -C.GOAL_WIDTH - (C.BALL_RADIUS * 2)
    max_x = C.GOAL_WIDTH + (C.BALL_RADIUS * 2)

    for _, row in df.iterrows():
        player = row["player_name"]
        side = name_to_team.get(player, None)
        if side is None:
            print(f"WARNING: No side associated with player {player}")

        goal_y = C.FIELD_Y if side == "blue" else -C.FIELD_Y

        # filter out touches where the ball is not moving downfield
        if side == "blue" and row.get("ball_vy", 0) < 0:
            continue
        if side == "orange" and row.get("ball_vy", 0) > 0:
            continue

        shot_rows = {
            "frame": row.get("frame"),
            "player_name": player,
            "team": side,
            "goal_y": goal_y,
            "ball_vy": row.get("ball_vy", 0),
            "dist_to_ball": row.get("dist_to_ball"),
            "impact_frame": row.get("impact_frame"),
            "impact_impulse": row.get("impact_impulse"),
        }
        shots.append(shot_rows)

    shot_df = pd.DataFrame(shots)
    if shot_df.empty:
        return ShotTable(
            pd.DataFrame(
                columns=[
                    "frame",
                    "player_name",
                    "team",
                    "goal_y",
                    "ball_vy",
                    "dist_to_ball",
                    "impact_frame",
                    "impact_impulse",
                ]
            )
        )

    return ShotTable(shot_df)


def near_net(touch_df: TouchTable, frame_df: FrameTable, name_to_team: dict, team: int):
    touches = touch_df.df.reset_index(drop=True)
    frames = frame_df.df

    frame_numbers = frames["frame"].to_numpy()
    bx = frames["ball_x"].to_numpy()
    by = frames["ball_y"].to_numpy()
    bz = frames["ball_z"].to_numpy()
    bvy = frames["ball_vy"].to_numpy()

    is_orange = team == C.ORANGE_TEAM
    target_y = C.FIELD_Y if is_orange else -C.FIELD_Y
    team_str = "orange" if is_orange else "blue"

    # cylindrical bounding box
    MAX_Z = C.GOAL_HEIGHT * 2
    THREAT_RADIUS = 2000
    clamped_x = np.clip(bx, -C.GOAL_HALF_WIDTH, C.GOAL_HALF_WIDTH)

    # 2D distance squared from the closest point on the goal line
    dist_xy_sq = (bx - clamped_x) ** 2 + (by - target_y) ** 2

    # check if within distance radius and acceptable height
    in_box = (
        (dist_xy_sq <= THREAT_RADIUS**2)
        & (bz >= 0)
        & (bz <= MAX_Z)
    )

    # detect edge transitions from not in box to in box
    entered_box = in_box & ~np.concatenate(([False], in_box[:-1]))

    candidate_entries = []
    for i in range(len(touches)):
        touch = touches.iloc[i]

        if name_to_team.get(touch["player_name"]) == team_str:
            continue

        start_frame = touch["frame"]
        if i + 1 < len(touches):
            end_frame = touches.iloc[i + 1]["frame"]
        else:
            end_frame = frame_numbers[-1] + 1

        start_idx = np.searchsorted(frame_numbers, start_frame)
        end_idx = np.searchsorted(frame_numbers, end_frame)

        if start_idx >= end_idx:
            continue

        # find all boundary entries within this slice
        window_crossings = np.where(entered_box[start_idx:end_idx])[0] + start_idx
        entry_indices = list(window_crossings)

        # Edge case: ball was already in the threat zone at the moment of touch
        if in_box[start_idx] and start_idx not in entry_indices:
            entry_indices.insert(0, start_idx)

        # filter out entries moving away from the net as they cant be shots
        for idx in entry_indices:
            toward_net = (bvy[idx] > 0) if is_orange else (bvy[idx] < 0)

            if toward_net:
                candidate_entries.append(
                    {
                        "touch_frame": start_frame,
                        "entry_frame": frame_numbers[idx],
                        "player_name": touch["player_name"],
                        "ball_pos": (bx[idx], by[idx], bz[idx]),
                        "ball_vel_y": bvy[idx],
                        "is_initial_touch": (idx == start_idx),
                    }
                )

    return candidate_entries
