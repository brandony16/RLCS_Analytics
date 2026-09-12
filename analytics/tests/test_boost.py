import pandas as pd
import pytest

from src.analysis.boost import calculate_boost_usage


def test_reset_event_breaks_boost_continuity_without_exact_player_row():
    frames = pd.DataFrame(
        {
            "frame": [1, 4, 5],
            "player_name": ["Player", "Player", "Player"],
            "boost_amount": [80.0, 33.33, 32.22],
        }
    )
    events = [{"type": "reset", "frame": 3}]

    result = calculate_boost_usage(frames, events=events)

    assert result.loc[result["frame"] == 4, "is_reset_boundary"].item()
    assert result.loc[result["frame"] == 4, "boost_used"].item() == 0.0
    assert result.loc[result["frame"] == 5, "boost_used"].item() == pytest.approx(1.11)


def test_normal_decrease_counts_without_reset_event():
    frames = pd.DataFrame(
        {
            "frame": [1, 2],
            "player_name": ["Player", "Player"],
            "boost_amount": [50.0, 48.0],
        }
    )

    result = calculate_boost_usage(frames)

    assert not result.loc[result["frame"] == 2, "is_reset_boundary"].item()
    assert result.loc[result["frame"] == 2, "boost_used"].item() == 2.0
