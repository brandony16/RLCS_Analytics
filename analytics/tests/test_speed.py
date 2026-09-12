import pandas as pd
import numpy as np
from src.analysis.speed import calculate_speeds

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