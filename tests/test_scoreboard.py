from src.features.scoreboard import flatten_player_stats


def test_flatten_player_stats():
    # Mock data structure matching the JSON PlayerStats metadata
    mock_stats = [
        {
            "Name": "Baby Sparta",
            "Team": 1,
            "Score": 1194,
            "Goals": 5,
            "Saves": 5,
            "Shots": 12,
            "PlayerID": {"name": "UniqueNetId", "fields": {"Uid": "0"}},
        }
    ]

    result = flatten_player_stats(mock_stats)

    assert result[0]["player_name"] == "Baby Sparta"
    assert result[0]["team"] == 1
    assert result[0]["score"] == 1194
    assert result[0]["goals"] == 5
    assert result[0]["saves"] == 5
    assert result[0]["shots"] == 12


def test_flatten_multiple_players():
    """Ensure all players in the list are processed correctly."""
    mock_stats = [
        {"Name": "Player 1", "Score": 100},
        {"Name": "Player 2", "Score": 200},
    ]
    result = flatten_player_stats(mock_stats)

    assert len(result) == 2
    assert result[0]["player_name"] == "Player 1"
    assert result[1]["player_name"] == "Player 2"


def test_flatten_missing_stats():
    """
    Ensure the script doesn't crash if a field is missing.
    In real replays, sometimes a player disconnects or stats aren't recorded.
    """
    mock_stats = [{"Name": "Newbie"}]  # Missing Score, Goals, etc.
    result = flatten_player_stats(mock_stats)

    # Assert defaults are applied
    assert result[0]["player_name"] == "Newbie"
    assert result[0]["score"] == 0
    assert result[0]["goals"] == 0


def test_flatten_empty_list():
    """Ensure an empty list of stats returns an empty list."""
    assert flatten_player_stats([]) == []
