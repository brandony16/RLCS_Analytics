import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class ActorObservation:
    """Useful actor data that can be resolved after a delayed network link."""

    frame: int
    time: float
    delta: float
    game_time: float
    actor_id: int
    attribute_name: str
    attributes: Dict[str, Any]


def save_metadata(raw_data: Dict[str, Any], match_guid: str, output_dir: str) -> str:
    metadata: Dict[str, Any] = {
        "properties": raw_data.get("properties", {}),
        "tick_marks": raw_data.get("tick_marks", []),
        "demos": raw_data.get("demos", {}),
    }
    metadata_path = os.path.join(output_dir, f"{match_guid}_metadata.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
    return metadata_path


def object_name(global_objects: List[str], object_id: Optional[int]) -> str:
    if object_id is None or object_id < 0 or object_id >= len(global_objects):
        return ""
    return global_objects[object_id]


def actor_id_from_deleted_actor(actor: Any) -> Optional[int]:
    if isinstance(actor, dict):
        return actor.get("actor_id")
    if isinstance(actor, int):
        return actor
    return None


def active_actor_id(attributes: Dict[str, Any]) -> Optional[int]:
    active_actor = attributes.get("ActiveActor", {})
    if not active_actor or active_actor.get("active") is False:
        return None
    actor_id = active_actor.get("actor")
    if actor_id is None or actor_id < 0:
        return None
    return actor_id


def remove_actor_links(
    actor_id: int,
    player_names: Dict[int, str],
    car_to_pri: Dict[int, int],
    component_to_car: Dict[int, int],
    actor_object_names: Dict[int, str],
) -> None:
    player_names.pop(actor_id, None)
    car_to_pri.pop(actor_id, None)
    component_to_car.pop(actor_id, None)
    for component_id, car_id in list(component_to_car.items()):
        if car_id == actor_id:
            component_to_car.pop(component_id, None)
    for car_id, pri_id in list(car_to_pri.items()):
        if pri_id == actor_id:
            car_to_pri.pop(car_id, None)
    actor_object_names.pop(actor_id, None)


def apply_link_update(
    actor_id: int,
    attribute_name: str,
    attributes: Dict[str, Any],
    player_names: Dict[int, str],
    car_to_pri: Dict[int, int],
    component_to_car: Dict[int, int],
) -> None:
    if attribute_name == "Engine.PlayerReplicationInfo:PlayerName":
        player_names[actor_id] = attributes.get("String", "Unknown")
    elif attribute_name == "Engine.Pawn:PlayerReplicationInfo":
        pri_id = active_actor_id(attributes)
        if pri_id is None:
            car_to_pri.pop(actor_id, None)
        else:
            car_to_pri[actor_id] = pri_id
    elif attribute_name == "TAGame.CarComponent_TA:Vehicle":
        parent_car_id = active_actor_id(attributes)
        if parent_car_id is None:
            component_to_car.pop(actor_id, None)
        else:
            component_to_car[actor_id] = parent_car_id


def is_useful_observation(attribute_name: str, attributes: Dict[str, Any]) -> bool:
    return (
        "RigidBody" in attributes
        or "ReplicatedBoost" in attributes
        or attribute_name == "TAGame.CarComponent_Dodge_TA:DodgeTorque"
    )


def resolve_observation(
    observation: ActorObservation,
    actor_object_names: Dict[int, str],
    car_to_pri: Dict[int, int],
    component_to_car: Dict[int, int],
    player_names: Dict[int, str],
) -> Optional[Tuple[int, str]]:
    actor_id = observation.actor_id
    target_id = component_to_car.get(actor_id, actor_id)
    pri_id = car_to_pri.get(target_id)
    if pri_id is not None and pri_id in player_names:
        return target_id, player_names[pri_id]
    if actor_object_names.get(actor_id, "").startswith("Archetypes.Ball."):
        return target_id, "Ball"
    return None


def add_observation_to_row(
    row: Dict[str, Any], observation: ActorObservation
) -> None:
    attributes = observation.attributes
    if "RigidBody" in attributes:
        rigid_body = attributes["RigidBody"]
        location = rigid_body.get("location") or {}
        rotation = rigid_body.get("rotation") or {}
        linear_velocity = rigid_body.get("linear_velocity") or {}
        row.update(
            {
                "loc_x": location.get("x"),
                "loc_y": location.get("y"),
                "loc_z": location.get("z"),
                "rot_x": rotation.get("x"),
                "rot_y": rotation.get("y"),
                "rot_z": rotation.get("z"),
                "lin_vel_x": linear_velocity.get("x"),
                "lin_vel_y": linear_velocity.get("y"),
                "lin_vel_z": linear_velocity.get("z"),
            }
        )
        row["has_useful_data"] = True
    if "ReplicatedBoost" in attributes:
        raw_boost = attributes["ReplicatedBoost"].get("boost_amount", 0)
        row["boost_amount"] = round((raw_boost / 255.0) * 100, 2)
        row["has_useful_data"] = True
    if observation.attribute_name == "TAGame.CarComponent_Dodge_TA:DodgeTorque":
        row["is_dodging"] = 1
        row["has_useful_data"] = True


def parse_network_frames(
    data: Dict[str, Any], match_guid: str
) -> Tuple[List[Dict[str, Any]], Dict[int, str], Dict[int, int], int]:
    global_objects: List[str] = data.get("objects", [])
    network_frames: List[Dict[str, Any]] = data.get("network_frames", {}).get("frames", [])
    player_names: Dict[int, str] = {}
    car_to_pri: Dict[int, int] = {}
    component_to_car: Dict[int, int] = {}
    actor_object_names: Dict[int, str] = {}
    pending_observations: List[ActorObservation] = []
    rows: Dict[Tuple[int, int], Dict[str, Any]] = {}
    processed_demos: Dict[Tuple[int, int], float] = {}
    demo_counts: Dict[int, int] = {}
    game_time = 0.0

    print(f"Parsing {len(network_frames)} network frames...")
    for frame_index, frame in enumerate(network_frames):
        time: float = frame.get("time", 0.0)
        delta: float = frame.get("delta", 0.0)
        if frame_index > 0:
            game_time += delta

        for deleted_actor in frame.get("deleted_actors", []):
            deleted_id = actor_id_from_deleted_actor(deleted_actor)
            if deleted_id is not None:
                remove_actor_links(
                    deleted_id,
                    player_names,
                    car_to_pri,
                    component_to_car,
                    actor_object_names,
                )

        for actor in frame.get("new_actors", []):
            actor_id = actor.get("actor_id")
            if actor_id is not None:
                actor_object_names[actor_id] = object_name(
                    global_objects, actor.get("object_id")
                )

        updated_observations: List[ActorObservation] = []
        for actor in frame.get("updated_actors", []):
            actor_id: int = actor.get("actor_id")
            attributes: Dict[str, Any] = actor.get("attribute", {})
            attribute_name = object_name(global_objects, actor.get("object_id"))
            actor_object_names.setdefault(actor_id, attribute_name)
            apply_link_update(
                actor_id,
                attribute_name,
                attributes,
                player_names,
                car_to_pri,
                component_to_car,
            )

            if attribute_name == "TAGame.Car_TA:ReplicatedDemolishExtended":
                demolish_data = attributes.get("DemolishExtended", {})
                attacker_pri_id = demolish_data.get("attacker_pri", {}).get("actor")
                victim_id = demolish_data.get("victim", {}).get("actor")
                if attacker_pri_id is not None and attacker_pri_id != -1 and victim_id is not None:
                    demo_key = (attacker_pri_id, victim_id)
                    last_seen_time = processed_demos.get(demo_key)
                    if last_seen_time is None or time - last_seen_time > 5.0:
                        demo_counts[attacker_pri_id] = demo_counts.get(attacker_pri_id, 0) + 1
                        processed_demos[demo_key] = time

            if is_useful_observation(attribute_name, attributes):
                updated_observations.append(
                    ActorObservation(
                        frame_index,
                        time,
                        delta,
                        game_time,
                        actor_id,
                        attribute_name,
                        attributes,
                    )
                )

        observations = pending_observations + updated_observations
        pending_observations = []
        for observation in observations:
            resolved = resolve_observation(
                observation,
                actor_object_names,
                car_to_pri,
                component_to_car,
                player_names,
            )
            if resolved is None:
                pending_observations.append(observation)
                continue
            target_id, player_name = resolved
            row_key = (observation.frame, target_id)
            if row_key not in rows:
                rows[row_key] = {
                    "match_guid": match_guid,
                    "frame": observation.frame,
                    "time": observation.time,
                    "delta": observation.delta,
                    "game_time": observation.game_time,
                    "player_name": player_name,
                    "has_useful_data": False,
                }
            add_observation_to_row(rows[row_key], observation)

        if frame_index % 1000 == 0 and frame_index > 0:
            print(f"Processed {frame_index} frames...")

    if pending_observations:
        print(
            f"Warning: {len(pending_observations)} useful observations "
            "could not be linked to a player or ball."
        )
    parsed_rows = [row for row in rows.values() if row.pop("has_useful_data", False)]
    return parsed_rows, player_names, demo_counts, len(network_frames)


def parse_and_save_replay(
    input_json_path: str, output_dir: str = "data/processed"
) -> None:
    print(f"Loading {input_json_path}...")
    with open(input_json_path, "r", encoding="utf-8-sig") as file:
        data: Dict[str, Any] = json.load(file)

    properties: Dict[str, Any] = data.get("properties", {})
    match_guid: str = properties.get("MatchGUID", "Unknown_Match")
    expected_frames: int = properties.get("NumFrames", 0)
    csv_output_path = os.path.join(output_dir, f"{match_guid}_frames.csv")
    parsed_rows, player_names, demo_counts, frames_parsed_count = parse_network_frames(
        data, match_guid
    )
    df = pd.DataFrame(parsed_rows)

    print("Applying forward fill to continuous player state data...")
    df = df.sort_values(by=["player_name", "time"])
    is_player = df["player_name"] != "Ball"
    continuous_cols = [
        "loc_x", "loc_y", "loc_z", "rot_x", "rot_y", "rot_z",
        "lin_vel_x", "lin_vel_y", "lin_vel_z", "boost_amount",
    ]
    if "is_dodging" in df.columns:
        df["is_dodging"] = df["is_dodging"].fillna(0)
    else:
        df["is_dodging"] = 0
    df.loc[is_player, continuous_cols] = (
        df.loc[is_player].groupby("player_name")[continuous_cols].ffill()
    )
    df.loc[is_player, "boost_amount"] = df.loc[is_player, "boost_amount"].fillna(33.33)
    is_ball = df["player_name"] == "Ball"
    ball_cols = continuous_cols[:-1]
    df.loc[is_ball, ball_cols] = (
        df.loc[is_ball].groupby("player_name")[ball_cols].ffill()
    )

    data["demos"] = {
        player_names.get(pri_id, f"Unknown_{pri_id}"): count
        for pri_id, count in demo_counts.items()
    }
    save_metadata(data, match_guid, output_dir)
    df = df.sort_values(by=["time"])
    df["time"] = df["time"] - df["time"].iloc[0]
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(csv_output_path, index=False)

    print(f"\nSuccessfully processed match: {match_guid}")
    print(f"Physics CSV: {csv_output_path}")
    print(f"Expected Frames: {expected_frames}")
    print(f"Actual Frames Parsed: {frames_parsed_count}")
    print(f"Total Useful Rows: {len(df)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_json>")
    else:
        parse_and_save_replay(sys.argv[1])
