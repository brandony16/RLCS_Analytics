import matplotlib.pyplot as plt
from typing import List, Dict, Any
from matplotlib.ticker import FuncFormatter
from pandas import DataFrame

from src.analysis.speed import calculate_speeds


def show_boost_by_player_graph(
    df: DataFrame, events: List[Dict[str, Any]], player_names: List[str]
):
    for player, player_df in df.groupby("player_name"):
        if player in player_names:
            plt.plot(player_df["game_time"], player_df["boost_amount"], label=player)

    plt.axhline(y=33.33, color="blue", linestyle=":", label="Starting Boost")

    for event in events:
        if event.get("type") == "goal":
            frame = df[df["frame"] == event.get("frame")]
            time = frame.iloc[0]["game_time"]
            team = "Blue" if event["team"] == 0 else "Orange"
            plt.axvline(x=time, color="green", linestyle=":")
            plt.text(time, 100, f"Goal - {team}", rotation=90, va="top")
        if event.get("type") == "demo":
            victim = event.get("victim_name")
            if victim in player_names:
                frame = df[df["frame"] == event.get("frame")]
                time = frame.iloc[0]["game_time"]
                plt.axvline(x=time, color="red", linestyle=":")
                plt.text(
                    time,
                    100,
                    event.get("victim_name") + " demoed",
                    rotation=90,
                    va="top",
                )

    plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, pos: _format_time(x)))

    plt.xlabel("Time")
    plt.ylabel("Boost")
    plt.title("Boost Over Time")
    plt.legend()
    plt.show()


def show_speed_by_player_graph(
    df: DataFrame, events: List[Dict[str, Any]], player_names: List[str]
):
    df = calculate_speeds(df)

    for player, player_df in df.groupby("player_name"):
        if player in player_names:
            plt.plot(player_df["game_time"], player_df["speed_uu"], label=player)

    plt.axhline(y=0, color="red", linestyle="-")
    plt.axhline(y=2300, color="red", linestyle="-")

    for event in events:
        if event.get("type") == "goal":
            frame = df[df["frame"] == event.get("frame")]
            time = frame.iloc[0]["game_time"]
            team = "Blue" if event["team"] == 0 else "Orange"
            plt.axvline(x=time, color="green", linestyle=":")
            plt.text(time, 2300, f"Goal - {team}", rotation=90, va="top")
        if event.get("type") == "demo":
            victim = event.get("victim_name")
            if victim in player_names:
                frame = df[df["frame"] == event.get("frame")]
                time = frame.iloc[0]["game_time"]
                plt.axvline(x=time, color="red", linestyle=":")
                plt.text(
                    time,
                    2300,
                    event.get("victim_name") + " demoed",
                    rotation=90,
                    va="top",
                )

    plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, pos: _format_time(x)))

    plt.xlabel("Time")
    plt.ylabel("Speed (uu/s)")
    plt.title("Speed Over Time")
    plt.legend()
    plt.show()


def _format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"
