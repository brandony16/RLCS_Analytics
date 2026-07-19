from backend.src.analytics.features.scoreboard import flatten_player_stats


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
    # Simulate the parsed demo counts mapping
    mock_demos = {"Baby Sparta": 4}

    result = flatten_player_stats(mock_stats, mock_demos)

    assert result[0]["player_name"] == "Baby Sparta"
    assert result[0]["team"] == 1
    assert result[0]["score"] == 1194
    assert result[0]["goals"] == 5
    assert result[0]["saves"] == 5
    assert result[0]["shots"] == 12
    assert result[0]["demos"] == 4  # Verify demo count matches


def test_flatten_multiple_players():
    """Ensure all players in the list are processed correctly and demos map correctly."""
    mock_stats = [
        {"Name": "Player 1", "Score": 100},
        {"Name": "Player 2", "Score": 200},
    ]
    mock_demos = {"Player 2": 3}  # Player 1 has no demos

    result = flatten_player_stats(mock_stats, mock_demos)

    assert len(result) == 2
    assert result[0]["player_name"] == "Player 1"
    assert result[0]["demos"] == 0  # Missing player defaults to 0

    assert result[1]["player_name"] == "Player 2"
    assert result[1]["demos"] == 3  # Matches dictionary count


def test_flatten_missing_stats():
    """
    Ensure the script doesn't crash if a field is missing.
    In real replays, sometimes a player disconnects or stats aren't recorded.
    """
    mock_stats = [{"Name": "Newbie"}]  # Missing Score, Goals, etc.
    result = flatten_player_stats(mock_stats, {})

    # Assert defaults are applied
    assert result[0]["player_name"] == "Newbie"
    assert result[0]["score"] == 0
    assert result[0]["goals"] == 0
    assert result[0]["demos"] == 0  # Verify missing demo defaults to 0


def test_flatten_empty_list():
    """Ensure an empty list of stats returns an empty list."""
    assert flatten_player_stats([], {}) == []
