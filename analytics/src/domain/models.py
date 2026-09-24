from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Sequence

import pandas as pd


@dataclass
class ActorObservation:
    """Useful actor data retained until its network links can be resolved."""

    frame: int
    time: float
    delta: float
    game_time: float
    actor_id: int
    attribute_name: str
    attributes: Dict[str, Any]


class SchemaTable:
    """Lightweight DataFrame wrapper with an explicit, discoverable schema.

    The wrapper keeps pandas ergonomics for analysis code while making each
    intermediate table self-documenting for future readers. Each subclass defines
    its required columns and property accessors for autocomplete-friendly field
    access.
    """

    required_columns: Sequence[str] = ()

    def __init__(self, df: pd.DataFrame):
        if df is None:
            raise ValueError("DataFrame is required")
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

        if df.empty:
            self.df = df.copy().reindex(columns=list(self.required_columns))
            return

        missing = [column for column in self.required_columns if column not in df.columns]
        if missing:
            raise ValueError(
                f"Missing required columns for {self.__class__.__name__}: {missing}"
            )

        self.df = df.copy()

    @property
    def schema(self) -> list[str]:
        return list(self.df.columns)

    @property
    def columns(self) -> list[str]:
        return list(self.df.columns)

    @property
    def rows(self) -> int:
        return len(self.df)

    def __dir__(self):
        return sorted(set(super().__dir__()) | set(self.df.columns) | set(self.__class__.__dict__.keys()))

    def __getattr__(self, name: str):
        return getattr(self.df, name)

    def __getitem__(self, key):
        return self.df[key]

    def __len__(self):
        return len(self.df)

    def __iter__(self):
        return iter(self.df)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(rows={len(self.df)}, "
            f"columns={list(self.df.columns)})"
        )

    def to_df(self) -> pd.DataFrame:
        return self.df.copy()


class FrameTable(SchemaTable):
    """Frame-level replay state after parsing and forward-filling.

    This is the core table that holds player and ball state per frame.
    """

    required_columns = (
        "frame",
        "time",
        "player_name",
        "loc_x",
        "loc_y",
        "loc_z",
        "lin_vel_x",
        "lin_vel_y",
        "lin_vel_z",
    )

    @property
    def frame(self) -> pd.Series:
        return self.df["frame"]

    @property
    def time(self) -> pd.Series:
        return self.df["time"]

    @property
    def delta(self) -> pd.Series:
        return self.df.get("delta", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def game_time(self) -> pd.Series:
        return self.df.get("game_time", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def player_name(self) -> pd.Series:
        return self.df["player_name"]

    @property
    def has_useful_data(self) -> pd.Series:
        return self.df.get("has_useful_data", pd.Series(index=self.df.index, dtype="bool"))

    @property
    def match_guid(self) -> pd.Series:
        return self.df.get("match_guid", pd.Series(index=self.df.index, dtype="object"))

    @property
    def loc_x(self) -> pd.Series:
        return self.df["loc_x"]

    @property
    def loc_y(self) -> pd.Series:
        return self.df["loc_y"]

    @property
    def loc_z(self) -> pd.Series:
        return self.df["loc_z"]

    @property
    def rot_x(self) -> pd.Series:
        return self.df.get("rot_x", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def rot_y(self) -> pd.Series:
        return self.df.get("rot_y", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def rot_z(self) -> pd.Series:
        return self.df.get("rot_z", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def lin_vel_x(self) -> pd.Series:
        return self.df["lin_vel_x"]

    @property
    def lin_vel_y(self) -> pd.Series:
        return self.df["lin_vel_y"]

    @property
    def lin_vel_z(self) -> pd.Series:
        return self.df["lin_vel_z"]

    @property
    def boost_amount(self) -> pd.Series:
        return self.df.get("boost_amount", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def is_dodging(self) -> pd.Series:
        return self.df.get("is_dodging", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_x(self) -> pd.Series:
        return self.df.get("ball_x", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_y(self) -> pd.Series:
        return self.df.get("ball_y", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_z(self) -> pd.Series:
        return self.df.get("ball_z", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_vx(self) -> pd.Series:
        return self.df.get("ball_vx", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_vy(self) -> pd.Series:
        return self.df.get("ball_vy", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_vz(self) -> pd.Series:
        return self.df.get("ball_vz", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_speed(self) -> pd.Series:
        return self.df.get("ball_speed", pd.Series(index=self.df.index, dtype="float64"))


class TouchTable(SchemaTable):
    """Player-ball contact episodes derived from frame-level tracking data."""

    required_columns = (
        "frame",
        "player_name",
        "dist_to_ball",
        "impact_frame",
        "impact_impulse",
    )

    @property
    def frame(self) -> pd.Series:
        return self.df["frame"]

    @property
    def player_name(self) -> pd.Series:
        return self.df["player_name"]

    @property
    def dist_to_ball(self) -> pd.Series:
        return self.df["dist_to_ball"]

    @property
    def impact_frame(self) -> pd.Series:
        return self.df["impact_frame"]

    @property
    def impact_impulse(self) -> pd.Series:
        return self.df["impact_impulse"]

    @property
    def ball_vy(self) -> pd.Series:
        return self.df.get("ball_vy", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def ball_speed(self) -> pd.Series:
        return self.df.get("ball_speed", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def impulse_window(self) -> pd.Series:
        return self.df.get("impulse_window", pd.Series(index=self.df.index, dtype="float64"))

    @property
    def possession_cluster_id(self) -> pd.Series:
        return self.df.get("possession_cluster_id", pd.Series(index=self.df.index, dtype="float64"))


class ScoreboardTable(SchemaTable):
    """Flattened match scoreboard metadata."""

    required_columns = (
        "player_name",
        "team",
        "score",
        "goals",
        "assists",
        "saves",
        "shots",
        "demos",
    )

    @property
    def player_name(self) -> pd.Series:
        return self.df["player_name"]

    @property
    def team(self) -> pd.Series:
        return self.df["team"]

    @property
    def score(self) -> pd.Series:
        return self.df["score"]

    @property
    def goals(self) -> pd.Series:
        return self.df["goals"]

    @property
    def assists(self) -> pd.Series:
        return self.df["assists"]

    @property
    def saves(self) -> pd.Series:
        return self.df["saves"]

    @property
    def shots(self) -> pd.Series:
        return self.df["shots"]

    @property
    def demos(self) -> pd.Series:
        return self.df["demos"]


class AggregateStatsTable(SchemaTable):
    """Grouped player summary stats after frame-level metrics are computed."""

    required_columns = (
        "player_name",
        "boost_usage",
        "avg_speed_kmh",
        "avg_speed_uu",
    )

    @property
    def player_name(self) -> pd.Series:
        return self.df["player_name"]

    @property
    def boost_usage(self) -> pd.Series:
        return self.df["boost_usage"]

    @property
    def avg_speed_kmh(self) -> pd.Series:
        return self.df["avg_speed_kmh"]

    @property
    def avg_speed_uu(self) -> pd.Series:
        return self.df["avg_speed_uu"]


class ShotTable(SchemaTable):
    """Shot-like touch events that are likely to be goal attempts."""

    required_columns = (
        "frame",
        "player_name",
        "team",
        "goal_y",
    )

    @property
    def frame(self) -> pd.Series:
        return self.df["frame"]

    @property
    def player_name(self) -> pd.Series:
        return self.df["player_name"]

    @property
    def team(self) -> pd.Series:
        return self.df["team"]

    @property
    def goal_y(self) -> pd.Series:
        return self.df["goal_y"]
