import json
import pandas as pd
import os


def parse_and_save_replay(input_json_path, output_csv_path):
    print(f"Loading {input_json_path}...")
    with open(input_json_path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)

    # 1. Extract Match Metadata
    properties = data.get("properties", {})
    match_guid = properties.get("MatchGUID", "Unknown_Match")
    map_name = properties.get("MapName", "Unknown_Map")
    expected_frames = properties.get("NumFrames", 0)

    # Extract Player Names and Teams for reference
    players = properties.get("PlayerStats", [])
    player_info = {
        p.get("Name"): {"Team": p.get("Team"), "Score": p.get("Score")} for p in players
    }
    print(f"Match Meta: {map_name} | Players: {list(player_info.keys())}")

    # 2. Extract Frame Data
    network_data = data.get("network_frames", {})
    network_frames = network_data.get("frames", [])
    parsed_rows = []

    print(f"Parsing {len(network_frames)} network frames... this may take a moment.")

    frames_parsed_count = 0

    for i, frame in enumerate(network_frames):
        # Print a progress update every 1000 frames so you know it hasn't crashed
        if i % 1000 == 0 and i > 0:
            print(f"Processed {i} frames...")

        time = frame.get("time")
        delta = frame.get("delta")
        frames_parsed_count += 1

        for actor in frame.get("updated_actors", []):
            actor_id = actor.get("actor_id")
            attributes = actor.get("attribute", {})

            if "RigidBody" in attributes:
                rb = attributes["RigidBody"]

                loc = rb.get("location") or {}
                rot = rb.get("rotation") or {}
                lin_vel = rb.get("linear_velocity") or {}
                ang_vel = rb.get("angular_velocity") or {}

                # Flatten the data, attaching the Match GUID so you can mix games later
                row = {
                    "match_guid": match_guid,
                    "time": time,
                    "delta": delta,
                    "actor_id": actor_id,
                    "loc_x": loc.get("x"),
                    "loc_y": loc.get("y"),
                    "loc_z": loc.get("z"),
                    "rot_x": rot.get("x"),
                    "rot_y": rot.get("y"),
                    "rot_z": rot.get("z"),
                    "lin_vel_x": lin_vel.get("x"),
                    "lin_vel_y": lin_vel.get("y"),
                    "lin_vel_z": lin_vel.get("z"),
                    "ang_vel_x": ang_vel.get("x"),
                    "ang_vel_y": ang_vel.get("y"),
                    "ang_vel_z": ang_vel.get("z"),
                }
                parsed_rows.append(row)

    # 3. Convert to DataFrame and Save
    df = pd.DataFrame(parsed_rows)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    # Save to CSV
    df.to_csv(output_csv_path, index=False)
    print(f"Successfully saved {len(df)} rows to {output_csv_path}")

    # 4. CHECKSUM & VALIDATION OUTPUT
    unique_actors = df["actor_id"].nunique() if not df.empty else 0

    print("\n" + "=" * 40)
    print("      PARSING CHECKSUM & SUMMARY      ")
    print("=" * 40)
    print(f"Expected Frames (Header): {expected_frames}")
    print(f"Actual Frames Parsed:     {frames_parsed_count}")

    if expected_frames == frames_parsed_count:
        print("✅ CHECKSUM PASSED: Frame counts match perfectly!")
    else:
        print("⚠️ WARNING: Parsed frames do not match header expected frames.")

    print("-" * 40)
    print(f"Total Physics Data Rows:  {len(df)}")
    print(f"Unique Actors Tracked:    {unique_actors}")
    print(f"File Saved To:            {output_csv_path}")
    print("=" * 40 + "\n")


parse_and_save_replay("data/json/sample_game.json", "data/processed/sample_game.csv")
