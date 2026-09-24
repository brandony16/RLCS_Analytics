import pandas as pd
import pytest

from src.analysis.touches import get_touch_df
from src.domain.models import FrameTable, TouchTable


def _frame(frame, player_name, velocity_x, ball=False):
    return {
        "frame": frame,
        "time": frame / 30,
        "player_name": "Ball" if ball else player_name,
        "loc_x": 0.0,
        "loc_y": 0.0,
        "loc_z": 0.0,
        "lin_vel_x": velocity_x,
        "lin_vel_y": 0.0,
        "lin_vel_z": 0.0,
    }


def test_touch_allows_impulse_to_arrive_near_contact_frame():
    rows = []
    for frame, velocity in enumerate([0.0, 0.0, 500.0, 500.0]):
        rows.append(_frame(frame, "Player", velocity, ball=True))
        rows.append(_frame(frame, "Player", 0.0))

    touches = get_touch_df(pd.DataFrame(rows), impulse_window=1)

    assert len(touches) == 1
    assert touches.iloc[0]["player_name"] == "Player"
    assert touches.iloc[0]["frame"] in {1, 2}
    assert touches.iloc[0]["impact_frame"] == 2
    assert touches.iloc[0]["impact_impulse"] >= 250


def test_adjacent_candidates_are_one_touch_episode():
    rows = []
    for frame, velocity in enumerate([0.0, 500.0, 800.0, 800.0, 800.0]):
        rows.append(_frame(frame, "Player", velocity, ball=True))
        rows.append(_frame(frame, "Player", 0.0))

    touches = get_touch_df(pd.DataFrame(rows), impulse_window=0, cluster_gap=2)

    assert len(touches) == 1
    assert touches.iloc[0]["possession_cluster_id"] == 1


def test_post_impact_proximity_is_not_counted_as_a_touch():
    rows = []
    for frame, velocity in enumerate([0.0, 500.0, 500.0, 500.0]):
        rows.append(_frame(frame, "Player", velocity, ball=True))
        rows.append(_frame(frame, "Player", 0.0))

    # The player is close only after the ball's impulse has already occurred.
    for row in rows:
        if row["player_name"] == "Player":
            row["loc_x"] = 1000.0
    rows[-1]["loc_x"] = 100.0
    touches = get_touch_df(pd.DataFrame(rows), impulse_window=1)

    assert touches.empty


def test_frame_table_validates_required_columns():
    df = pd.DataFrame([
        {"frame": 1, "player_name": "Player", "loc_x": 0.0, "loc_y": 0.0}
    ])

    with pytest.raises(ValueError, match="Missing required columns"):
        FrameTable(df)


def test_touch_table_preserves_dataframe_accessors():
    df = pd.DataFrame([
        {
            "frame": 1,
            "player_name": "Player",
            "dist_to_ball": 10.0,
            "impact_frame": 1,
            "impact_impulse": 300.0,
        }
    ])

    touches = TouchTable(df)

    assert len(touches) == 1
    assert touches.df.iloc[0]["player_name"] == "Player"
    assert touches["dist_to_ball"].iloc[0] == 10.0
    assert touches.player_name.iloc[0] == "Player"
