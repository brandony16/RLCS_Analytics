import pandas as pd
from pandas import DataFrame
import constants as C
import numpy as np

from src.domain.models import ShotTable, TouchTable, FrameTable


def get_shots(touch_df: TouchTable | DataFrame, name_to_team: dict, frame_df: FrameTable) -> ShotTable:
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
        return ShotTable(pd.DataFrame(columns=[
            "frame",
            "player_name",
            "team",
            "goal_y",
            "ball_vy",
            "dist_to_ball",
            "impact_frame",
            "impact_impulse",
        ]))

    return ShotTable(shot_df)

def near_orange_net(touch_df: TouchTable, frame_df: FrameTable, name_to_team: dict):
    Z_BOUND = (0, C.GOAL_HEIGHT + 4 * C.BALL_RADIUS)
    X_BOUND = (-C.GOAL_WIDTH - 4 * C.BALL_RADIUS, C.GOAL_WIDTH + 4 * C.BALL_RADIUS)
    Y_BOUND = (C.FIELD_Y - C.CORNER_OFFSET * 2, C.FIELD_Y)

    touches = touch_df.df.reset_index(drop=True)
    frames = frame_df.df

    frame_numbers = frames["frame"].to_numpy()
    bx = frames["ball_x"].to_numpy()
    by = frames["ball_y"].to_numpy()
    bz = frames["ball_z"].to_numpy()
    bvy = frames["ball_vy"].to_numpy()

    in_orange_box = (
        (X_BOUND[0] <= bx)
        & (bx <= X_BOUND[1])
        & (Y_BOUND[0] <= by)
        & (by <= Y_BOUND[1])
        & (Z_BOUND[0] <= bz)
        & (bz <= Z_BOUND[1])
    )

    # Transisitions from out of box to in box
    entered_box = in_orange_box & ~np.concatenate(([False], in_orange_box[:-1]))

    candidate_entries = []
    for i in range(len(touches)):
        touch = touches.iloc[i]

        if name_to_team.get(touch["player_name"]) == "orange":
            continue

        start_frame = touch["frame"]
        if i + 1 < len(touches):
            end_frame = touches.iloc[i + 1]["frame"]
        else:
            end_frame = frame_numbers[-1] + 1

        touch_window = (frame_numbers >= start_frame) & (frame_numbers < end_frame)
        window_indices = np.where(touch_window)[0]

        if len(window_indices) == 0:
            continue

        start_idx = window_indices[0]

        # find all times ball went from not in box to in box for this window
        crossing_mask = touch_window & entered_box
        entry_indices = list(np.where(crossing_mask)[0])

        # handle edge case where ball was already in the box at the touch
        if in_orange_box[start_idx] and start_idx not in entry_indices:
            entry_indices.insert(0, start_idx)

        # filter out times where the ball is moving away from the net (-y vel)
        for idx in entry_indices:
            if bvy[idx] > 0:
                candidate_entries.append(
                    {
                        "touch_frame": start_frame,
                        "entry_frame": frame_numbers[idx],
                        "player_name": touch["player_name"],
                        "ball_pos": (bx[idx], by[idx], bz[idx]),
                        "ball_vel_y": bvy[idx],
                        # Flag whether this was the hit itself or a later entry
                        "is_initial_touch": (idx == start_idx),
                    }
                )

    return candidate_entries
        