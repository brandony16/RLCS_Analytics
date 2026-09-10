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

    rows, player_names, _, frame_count = parse_network_frames(data, "test-match")

    assert frame_count == 2
    assert player_names == {10: "Delayed Player"}
    assert len(rows) == 1
    assert rows[0]["frame"] == 0
    assert rows[0]["time"] == 10.0
    assert rows[0]["player_name"] == "Delayed Player"
    assert rows[0]["boost_amount"] == round((127 / 255) * 100, 2)


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

    rows, _, _, _ = parse_network_frames(data, "test-match")

    assert len(rows) == 1
    assert rows[0]["player_name"] == "Ball"
    assert rows[0]["loc_x"] == 1