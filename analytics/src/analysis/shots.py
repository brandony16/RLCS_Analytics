from pandas import DataFrame
import constants as C

from src.domain.models import TouchTable


def get_shots(touch_df: TouchTable | DataFrame, name_to_team: dict):
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
        if side == "blue" and row["ball_vy"] < 0:
            continue
        if side == "orange" and row["ball_vy"] > 0:
            continue
