import pandas as pd
import numpy as np
from backend.src.features.physics_calc import calculate_speeds, filter_impossible_speeds

def test_speed_calculation():
    """
    Validates that the 3D vector magnitude is calculated correctly
    and the conversion to km/h aligns with Rocket League physics logic.
    """
    mock_data = pd.DataFrame(
        {
            "lin_vel_x": [2300.0, 0.0, -1000.0],
            "lin_vel_y": [0.0, 1000.0, -1000.0],
            "lin_vel_z": [0.0, 0.0, 0.0],
        }
    )

    result = calculate_speeds(mock_data)

    # Frame 0: Moving purely on X axis at max speed
    assert result["speed_uu"].iloc[0] == 2300.0
    assert np.isclose(result["speed_kmh"].iloc[0], 82.8)

    # Frame 1: Moving purely on Y axis
    assert result["speed_uu"].iloc[1] == 1000.0
    assert np.isclose(result["speed_kmh"].iloc[1], 36.0)

    # Frame 2: Diagonal movement validation (Pythagorean theorem)
    expected_diagonal = np.sqrt((-1000) ** 2 + (-1000) ** 2)
    assert np.isclose(result["speed_uu"].iloc[2], expected_diagonal)


def test_filter_impossible_speeds():
    """
    Validates that demo respawns or lag teleportations (which result in
    massive frame-to-frame velocity spikes) are successfully dropped.
    """
    mock_data = pd.DataFrame(
        {
            "player_name": ["Baby Sparta", "Baby Sparta", "Tung Tung Tung Segna"],
            "speed_uu": [2000.0, 15000.0, 2350.0],  # 15000.0 is a teleport spike
        }
    )

    result = filter_impossible_speeds(mock_data)

    # The dataframe should only contain 2 rows now
    assert len(result) == 2

    # The teleportation spike must be completely gone
    assert 15000.0 not in result["speed_uu"].values

    # Valid high speeds should remain
    assert 2350.0 in result["speed_uu"].values
