from scripts.parse_json_replay import parse_network_frames


def test_observation_waits_for_delayed_component_and_player_links():
    data = {
        "objects": [
            "Archetypes.CarComponents.CarComponent_Boost",
            "Archetypes.Car.Car_Default",
            "Archetypes.Ball.Ball_Default",
            "Engine.PlayerReplicationInfo:PlayerName",
            "Engine.Pawn:PlayerReplicationInfo",
            "TAGame.CarComponent_TA:Vehicle",
            "TAGame.CarComponent_Boost_TA:ReplicatedBoost",
        ],
        "network_frames": {
            "frames": [
                {
                    "time": 10.0,
                    "delta": 0.0,
                    "new_actors": [
                        {"actor_id": 20, "object_id": 0},
                        {"actor_id": 30, "object_id": 1},
                        {"actor_id": 2, "object_id": 2},
                        {"actor_id": 10, "object_id": 3},
                    ],
                    "updated_actors": [
                        {
                            "actor_id": 20,
                            "object_id": 6,
                            "attribute": {
                                "ReplicatedBoost": {"boost_amount": 127}
                            },
                        }
                    ],
                },
                {
                    "time": 10.033,
                    "delta": 0.033,
                    "new_actors": [],
                    "updated_actors": [
                        {
                            "actor_id": 10,
                            "object_id": 3,
                            "attribute": {"String": "Delayed Player"},
                        },
                        {
                            "actor_id": 30,
                            "object_id": 4,
                            "attribute": {"ActiveActor": {"active": True, "actor": 10}},
                        },
                        {
                            "actor_id": 20,
                            "object_id": 5,
                            "attribute": {"ActiveActor": {"active": True, "actor": 30}},
                        },
                    ],
                },
            ]
        },
    }

    rows, player_names, _, events, frame_count = parse_network_frames(data, "test-match")

    assert frame_count == 2
    assert player_names == {10: "Delayed Player"}
    assert len(rows) == 1
    assert rows[0]["frame"] == 0
    assert rows[0]["time"] == 10.0
    assert rows[0]["player_name"] == "Delayed Player"
    assert rows[0]["boost_amount"] == round((127 / 255) * 100, 2)
    assert events == []


def test_ball_observation_does_not_wait_for_player_link():
    data = {
        "objects": [
            "Archetypes.Ball.Ball_Default",
            "TAGame.RBActor_TA:ReplicatedRBState",
        ],
        "network_frames": {
            "frames": [
                {
                    "time": 1.0,
                    "delta": 0.0,
                    "new_actors": [{"actor_id": 2, "object_id": 0}],
                    "updated_actors": [
                        {
                            "actor_id": 2,
                            "object_id": 1,
                            "attribute": {
                                "RigidBody": {
                                    "location": {"x": 1, "y": 2, "z": 3}
                                }
                            },
                        }
                    ],
                }
            ]
        },
    }

    rows, _, _, events, _ = parse_network_frames(data, "test-match")

    assert len(rows) == 1
    assert rows[0]["player_name"] == "Ball"
    assert rows[0]["loc_x"] == 1
    assert events == []


def test_event_metadata_preserves_goals_and_tick_marks():
    data = {
        "properties": {
            "Goals": [
                {"frame": 12, "PlayerName": "Scorer", "PlayerTeam": 1}
            ]
        },
        "tick_marks": [{"frame": 12, "description": "Team1Goal"}],
        "objects": [],
        "network_frames": {"frames": []},
    }

    _, _, _, events, _ = parse_network_frames(data, "test-match")

    assert events == [
        {
            "type": "goal",
            "frame": 12,
            "description": "Team1Goal",
            "player_name": "Scorer",
            "team": 1,
            "metadata_frame": 12,
        },
    ]


def test_demo_event_keeps_victim_identity_before_link_is_cleared():
    data = {
        "objects": [
            "Engine.PlayerReplicationInfo:PlayerName",
            "Engine.Pawn:PlayerReplicationInfo",
            "TAGame.Car_TA:ReplicatedDemolishExtended",
        ],
        "network_frames": {
            "frames": [
                {
                    "time": 1.0,
                    "delta": 0.0,
                    "new_actors": [],
                    "updated_actors": [
                        {
                            "actor_id": 10,
                            "object_id": 0,
                            "attribute": {"String": "Victim"},
                        },
                        {
                            "actor_id": 91,
                            "object_id": 1,
                            "attribute": {
                                "ActiveActor": {"active": True, "actor": 10}
                            },
                        },
                    ],
                },
                {
                    "time": 1.033,
                    "delta": 0.033,
                    "new_actors": [],
                    "updated_actors": [
                        {
                            "actor_id": 91,
                            "object_id": 2,
                            "attribute": {
                                "DemolishExtended": {
                                    "attacker_pri": {"active": True, "actor": 20},
                                    "victim": {"active": True, "actor": 91},
                                }
                            },
                        },
                        {
                            "actor_id": 91,
                            "object_id": 1,
                            "attribute": {
                                "ActiveActor": {"active": False, "actor": -1}
                            },
                        },
                    ],
                },
            ]
        },
    }

    _, _, demo_counts, events, _ = parse_network_frames(data, "test-match")

    assert demo_counts == {20: 1}
    assert events == [
        {
            "type": "demo",
            "frame": 1,
            "time": 1.033,
            "game_time": 0.033,
            "attacker_pri_id": 20,
            "attacker_name": None,
            "victim_car_id": 91,
            "victim_pri_id": 10,
            "victim_name": "Victim",
        }
    ]