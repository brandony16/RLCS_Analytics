import json
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.domain.models import ActorObservation
from src.parsing.actor_links import (
    active_actor_id,
    actor_id_from_deleted_actor,
    apply_link_update,
    object_name,
    remove_actor_links,
    resolve_observation,
)
from src.parsing.events import add_demo_event, add_reset_event, build_event_metadata
from src.parsing.frame_rows import add_observation_to_row, is_useful_observation


def save_metadata(
    raw_data: Dict[str, Any],
    match_guid: str,
    output_dir: str,
    events: List[Dict[str, Any]],
) -> str:
    metadata = {
        "properties": raw_data.get("properties", {}),
        "tick_marks": raw_data.get("tick_marks", []),
        "demos": raw_data.get("demos", {}),
        "events": events,
    }
    metadata_path = os.path.join(output_dir, f"{match_guid}_metadata.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
    return metadata_path


def parse_network_frames(
    data: Dict[str, Any], match_guid: str
) -> Tuple[
    List[Dict[str, Any]],
    Dict[int, str],
    Dict[int, int],
    List[Dict[str, Any]],
    int,
]:
    global_objects: List[str] = data.get("objects", [])
    network_frames: List[Dict[str, Any]] = data.get("network_frames", {}).get("frames", [])
    player_names: Dict[int, str] = {}
    car_to_pri: Dict[int, int] = {}
    component_to_car: Dict[int, int] = {}
    last_known_car_to_pri: Dict[int, int] = {}
    actor_object_names: Dict[int, str] = {}
    pending_observations: List[ActorObservation] = []
    rows: Dict[Tuple[int, int], Dict[str, Any]] = {}
    processed_demos: Dict[Tuple[int, int], float] = {}
    demo_counts: Dict[int, int] = {}
    events = build_event_metadata(data)
    game_time = 0.0

    print(f"Parsing {len(network_frames)} network frames...")
    for frame_index, frame in enumerate(network_frames):
        time: float = frame.get("time", 0.0)
        delta: float = frame.get("delta", 0.0)
        if frame_index > 0:
            game_time += delta

        deleted_actors = frame.get("deleted_actors", [])
        if delta == 0 and deleted_actors:
            add_reset_event(events, frame_index, time, game_time, len(deleted_actors))

        for deleted_actor in deleted_actors:
            deleted_id = actor_id_from_deleted_actor(deleted_actor)
            if deleted_id is not None:
                last_known_car_to_pri.pop(deleted_id, None)
                for car_id, pri_id in list(last_known_car_to_pri.items()):
                    if pri_id == deleted_id:
                        last_known_car_to_pri.pop(car_id, None)
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
                        victim_pri_id = car_to_pri.get(
                            victim_id, last_known_car_to_pri.get(victim_id)
                        )
                        add_demo_event(
                            events,
                            frame_index,
                            time,
                            game_time,
                            attacker_pri_id,
                            player_names.get(attacker_pri_id),
                            victim_id,
                            victim_pri_id,
                            player_names.get(victim_pri_id),
                        )

            apply_link_update(
                actor_id,
                attribute_name,
                attributes,
                player_names,
                car_to_pri,
                component_to_car,
            )
            if attribute_name == "Engine.Pawn:PlayerReplicationInfo":
                pri_id = active_actor_id(attributes)
                if pri_id is not None:
                    last_known_car_to_pri[actor_id] = pri_id

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
    events.sort(key=lambda event: (event.get("frame") is None, event.get("frame", 0)))
    return parsed_rows, player_names, demo_counts, events, len(network_frames)


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
    parsed_rows, player_names, demo_counts, events, frames_parsed_count = parse_network_frames(
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
    save_metadata(data, match_guid, output_dir, events)
    df = df.sort_values(by=["time"])
    df["time"] = df["time"] - df["time"].iloc[0]
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(csv_output_path, index=False)

    print(f"\nSuccessfully processed match: {match_guid}")
    print(f"Physics CSV: {csv_output_path}")
    print(f"Expected Frames: {expected_frames}")
    print(f"Actual Frames Parsed: {frames_parsed_count}")
    print(f"Total Useful Rows: {len(df)}")
