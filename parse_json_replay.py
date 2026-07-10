import json
import pandas as pd
import os
import sys

"""
ETL Pipeline: Rocket League JSON to Tabular CSV
-----------------------------------------------
This script transforms hierarchical rrrocket JSON replay data into a 
flat CSV suitable for data analysis (e.g., heatmaps, speed stats, xG models).

Data Flow:
1. Load raw JSON (with BOM handling).
2. Pass 1 (Metadata Mapping): Link internal engine Actor IDs to Player Names.
3. Pass 2 (Physics & State): Route per-actor updates to their parent entity 
   (e.g., routing boost component data back to the Car).
4. Post-Process (Forward Filling): Fill missing network snapshots to ensure 
   every row has a continuous physics/boost state.
"""


def parse_and_save_replay(input_json_path, output_csv_path):
    print(f"Loading {input_json_path}...")
    with open(input_json_path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)

    # Load metadata
    properties = data.get("properties", {})
    match_guid = properties.get("MatchGUID", "Unknown_Match")
    expected_frames = properties.get(
        "NumFrames", 0
    )  # used for confirming that parsing worked

    global_objects = data.get("objects", [])

    network_data = data.get("network_frames", {})
    network_frames = network_data.get("frames", [])
    parsed_rows = []

    # --- STATE TRACKING ---
    player_names = {}  # PRI Actor ID -> String Name
    car_to_pri = {}  # Car Actor ID -> PRI Actor ID
    component_to_car = {}  # Component Actor ID -> Car Actor ID

    print(f"Parsing {len(network_frames)} network frames...")
    frames_parsed_count = 0

    for i, frame in enumerate(network_frames):
        if i % 1000 == 0 and i > 0:
            print(f"Processed {i} frames...")

        time = frame.get("time")
        delta = frame.get("delta")
        frames_parsed_count += 1

        frame_entities = {}

        # Pass 1: Update all network links first
        for actor in frame.get("updated_actors", []):
            actor_id = actor.get("actor_id")
            object_id = actor.get("object_id")
            attributes = actor.get("attribute", {})

            attribute_name = ""
            if object_id is not None and object_id < len(global_objects):
                attribute_name = global_objects[object_id]

            if attribute_name == "Engine.PlayerReplicationInfo:PlayerName":
                player_names[actor_id] = attributes.get("String", "Unknown")

            elif attribute_name == "Engine.Pawn:PlayerReplicationInfo":
                pri_id = attributes.get("ActiveActor", {}).get("actor")
                car_to_pri[actor_id] = pri_id

            elif attribute_name == "TAGame.CarComponent_TA:Vehicle":
                parent_car_id = attributes.get("ActiveActor", {}).get("actor")
                component_to_car[actor_id] = parent_car_id

        # Pass 2: Extract data now that links are updated
        for actor in frame.get("updated_actors", []):
            actor_id = actor.get("actor_id")
            attributes = actor.get("attribute", {})

            # Route to correct parent entity
            target_id = component_to_car.get(actor_id, actor_id)
            pri_id = car_to_pri.get(target_id)

            # If it has a Player ID, grab the name. If not, it's the ball.
            if pri_id is not None:
                player_name = player_names.get(pri_id, f"Loading_Name_{pri_id}")
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

    """
    The json files only tell you when something updated, not what each value is continuously.
    We therefore need to forward fill values to get an accurate picture of the state at each frame.
    """
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

    df = df.sort_values(by=["time"])

    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df.to_csv(output_csv_path, index=False)

    # check that we have the same number of expected frames as parsed frames
    print("\n" + "=" * 40)
    print("      PARSING CHECKSUM & SUMMARY      ")
    print("=" * 40)
    print(f"Expected Frames: {expected_frames}")
    print(f"Actual Frames Parsed:     {frames_parsed_count}")
    print(f"Total Useful Rows:        {len(df)}")
    print(f"File Saved To:            {output_csv_path}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_json> <output_csv>")
    else:
        parse_and_save_replay(sys.argv[1], sys.argv[2])
