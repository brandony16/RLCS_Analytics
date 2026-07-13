import json
import pandas as pd
import os
import sys
from typing import Dict, Any, List, Optional

"""
ETL Pipeline: Rocket League JSON to Tabular CSV
-----------------------------------------------
This script transforms hierarchical rrrocket JSON replay data into a 
flat CSV suitable for data analysis (e.g., heatmaps, speed stats, xG models).
It also extracts a lightweight metadata JSON for static scoreboard stats.

Data Flow:
1. Load raw JSON (with BOM handling).
2. Extract and save static match metadata.
3. Pass 1 (Metadata Mapping): Link internal engine Actor IDs to Player Names.
4. Pass 2 (Physics & State): Route per-actor updates to their parent entity.
5. Post-Process (Forward Filling): Fill missing network snapshots.
"""


def save_metadata(raw_data: Dict[str, Any], match_guid: str, output_dir: str) -> str:
    """Extracts static metadata and saves it to <match_guid>_metadata.json"""
    metadata: Dict[str, Any] = {
        "properties": raw_data.get("properties", {}),
        "tick_marks": raw_data.get("tick_marks", []),
        "demos": raw_data.get("demos", {}),
    }

    metadata_path = os.path.join(output_dir, f"{match_guid}_metadata.json")
    os.makedirs(output_dir, exist_ok=True)

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    return metadata_path


def parse_and_save_replay(
    input_json_path: str, output_dir: str = "data/processed"
) -> None:
    print(f"Loading {input_json_path}...")
    with open(input_json_path, "r", encoding="utf-8-sig") as file:
        data: Dict[str, Any] = json.load(file)

    # 1. Identify Match and set output paths
    properties: Dict[str, Any] = data.get("properties", {})
    match_guid: str = properties.get("MatchGUID", "Unknown_Match")

    # Define output files based on GUID
    csv_output_path = os.path.join(output_dir, f"{match_guid}_frames.csv")

    # 2. Setup parsing variables
    properties: Dict[str, Any] = data.get("properties", {})
    match_guid: str = properties.get("MatchGUID", "Unknown_Match")
    expected_frames: int = properties.get("NumFrames", 0)

    global_objects: List[str] = data.get("objects", [])
    network_data: Dict[str, Any] = data.get("network_frames", {})
    network_frames: List[Dict[str, Any]] = network_data.get("frames", [])

    parsed_rows: List[Dict[str, Any]] = []

    # --- STATE TRACKING ---
    player_names: Dict[int, str] = {}  # PRI Actor ID -> String Name
    car_to_pri: Dict[int, int] = {}  # Car Actor ID -> PRI Actor ID
    component_to_car: Dict[int, int] = {}  # Component Actor ID -> Car Actor ID
    demo_counts = {}  # PRI -> Total Demos

    print(f"Parsing {len(network_frames)} network frames...")
    frames_parsed_count: int = 0

    for i, frame in enumerate(network_frames):
        if i % 1000 == 0 and i > 0:
            print(f"Processed {i} frames...")

        time: float = frame.get("time", 0.0)
        delta: float = frame.get("delta", 0.0)
        frames_parsed_count += 1

        frame_entities: Dict[int, Dict[str, Any]] = {}

        # Pass 1: Update all network links first
        for actor in frame.get("updated_actors", []):
            actor_id: int = actor.get("actor_id")
            object_id: Optional[int] = actor.get("object_id")
            attributes: Dict[str, Any] = actor.get("attribute", {})

            attribute_name: str = ""
            if object_id is not None and object_id < len(global_objects):
                attribute_name = global_objects[object_id]

            if attribute_name == "Engine.PlayerReplicationInfo:PlayerName":
                player_names[actor_id] = attributes.get("String", "Unknown")

            elif attribute_name == "Engine.Pawn:PlayerReplicationInfo":
                pri_id = attributes.get("ActiveActor", {}).get("actor")
                if pri_id is not None:
                    car_to_pri[actor_id] = pri_id

            elif attribute_name == "TAGame.CarComponent_TA:Vehicle":
                parent_car_id = attributes.get("ActiveActor", {}).get("actor")
                if parent_car_id is not None:
                    component_to_car[actor_id] = parent_car_id
            elif attribute_name == "TAGame.Car_TA:ReplicatedDemolishExtended":
                attacker_pri_id = (
                    attributes.get("DemolishExtended", {})
                    .get("attacker_pri", {})
                    .get("actor")
                )
                if attacker_pri_id is not None and attacker_pri_id != -1:
                    demo_counts[attacker_pri_id] = (
                        demo_counts.get(attacker_pri_id, 0) + 1
                    )

        # Pass 2: Extract data now that links are updated
        for actor in frame.get("updated_actors", []):
            actor_id: int = actor.get("actor_id")
            attributes: Dict[str, Any] = actor.get("attribute", {})

            # Route to correct parent entity
            target_id: int = component_to_car.get(actor_id, actor_id)
            pri_id: Optional[int] = car_to_pri.get(target_id)

            # If it has a Player ID, grab the name. If not, it's the ball.
            if pri_id is not None:
                player_name: str = player_names.get(pri_id, f"Loading_Name_{pri_id}")
            else:
                player_name = "Ball"

            # Skip Ghost entities and Replay Camera artifacts
            if "Loading_Name_" in player_name:
                continue

            if target_id not in frame_entities:
                frame_entities[target_id] = {
                    "match_guid": match_guid,
                    "time": time,
                    "delta": delta,
                    "player_name": player_name,
                    "has_useful_data": False,
                }

            row = frame_entities[target_id]

            # fill out physics data (location, speed, orientation)
            if "RigidBody" in attributes:
                rb = attributes["RigidBody"]
                loc = rb.get("location") or {}
                rot = rb.get("rotation") or {}
                lin_vel = rb.get("linear_velocity") or {}

                row.update(
                    {
                        "loc_x": loc.get("x"),
                        "loc_y": loc.get("y"),
                        "loc_z": loc.get("z"),
                        "rot_x": rot.get("x"),
                        "rot_y": rot.get("y"),
                        "rot_z": rot.get("z"),
                        "lin_vel_x": lin_vel.get("x"),
                        "lin_vel_y": lin_vel.get("y"),
                        "lin_vel_z": lin_vel.get("z"),
                    }
                )
                row["has_useful_data"] = True

            # extract boost info
            if "ReplicatedBoost" in attributes:
                boost_data = attributes["ReplicatedBoost"]
                raw_boost = boost_data.get("boost_amount", 0)
                row["boost_amount"] = round((raw_boost / 255.0) * 100, 2)
                row["has_useful_data"] = True

            attribute_name = ""
            if actor.get("object_id") is not None and actor.get("object_id") < len(
                global_objects
            ):
                attribute_name = global_objects[actor.get("object_id")]

            # see if the car is dodging
            if attribute_name == "TAGame.CarComponent_Dodge_TA:DodgeTorque":
                row["is_dodging"] = 1
                row["has_useful_data"] = True

        # add row only if it has actual data
        for row in frame_entities.values():
            if row.pop("has_useful_data", False):
                parsed_rows.append(row)

    df = pd.DataFrame(parsed_rows)

    print("Applying forward fill to continuous player state data...")
    df = df.sort_values(by=["player_name", "time"])

    is_player = df["player_name"] != "Ball"

    continuous_cols = [
        "loc_x",
        "loc_y",
        "loc_z",
        "rot_x",
        "rot_y",
        "rot_z",
        "lin_vel_x",
        "lin_vel_y",
        "lin_vel_z",
        "boost_amount",
    ]

    # Fill dodge with 0 if not present
    if "is_dodging" in df.columns:
        df["is_dodging"] = df["is_dodging"].fillna(0)
    else:
        df["is_dodging"] = 0

    # Forward fill all these columns for players
    df.loc[is_player, continuous_cols] = (
        df.loc[is_player].groupby("player_name")[continuous_cols].ffill()
    )

    # Set default starting boost if missing at the very beginning
    df.loc[is_player, "boost_amount"] = df.loc[is_player, "boost_amount"].fillna(33.33)

    # The Ball also needs its physics forward-filled
    is_ball = df["player_name"] == "Ball"
    ball_cols = continuous_cols[:-1]  # Everything except boost
    df.loc[is_ball, ball_cols] = (
        df.loc[is_ball].groupby("player_name")[ball_cols].ffill()
    )

    data["demos"] = {
        player_names.get(pri_id, f"Unknown_{pri_id}"): count
        for pri_id, count in demo_counts.items()
    }
    # save metadata
    save_metadata(data, match_guid, output_dir)

    df = df.sort_values(by=["time"])

    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(csv_output_path, index=False)

    print(f"\nSuccessfully processed match: {match_guid}")
    print(f"Physics CSV: {csv_output_path}")
    print("=" * 40 + "\n")

    os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
    df.to_csv(csv_output_path, index=False)

    print("\n" + "=" * 40)
    print("      PARSING CHECKSUM & SUMMARY      ")
    print("=" * 40)
    print(f"Expected Frames: {expected_frames}")
    print(f"Actual Frames Parsed:     {frames_parsed_count}")
    print(f"Total Useful Rows:        {len(df)}")
    print(f"File Saved To:            {csv_output_path}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_json>")
    else:
        parse_and_save_replay(sys.argv[1])
