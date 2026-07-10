# rrrocket JSON Output Structure

This file outlines how the json files output by rrrocket are parsed. These files are under the path ./data/json

## Overview

[rrrocket](https://github.com/nickbabcock/rrrocket) parses a binary `.replay` files into a readable json format. The data is partitioned into two distinct categories: Static Metadata (game properties) and Dynamic Network Frames (frame-by-frame state).

### 1. Static Metadata

Located at the root of the JSON object, this contains useful metadata on the game. \
To see all available metadata, its easiest to run:

```
./rrrocket.exe -p data/raw/<replay-file>.replay > <output-file>.json
```

This omits network frames and is just pure metadata.

**Metadata Highlights**

- `properties`:
  - `TeamSize`: Size of each team (1, 2, 3)
  - `Team0Score`/`Team1Score`: The final score for each team (0 = blue, 1 = orange)
  - `TotalSecondsPlayed`: The length of the match (300 seconds + overtime)
  - `Goals`: A list of goal events, with each event having the `frame` at which the goal occured, the `PlayerName` of who scored the goal, and the `PlayerTeam` who scored
  - `HighLights`: A list of significant events in the game. Each event has a `frame` at which it occured, a `CarName` and `BallName` of the internal names of the objects involved, and a `GoalActorName` that is a flag that determines if a goal was scored.
  - `PlayerStats`: A list of objects containing metadata and final stats for each player
  - `MapName`: The name of the map where the game took place
  - Other metadata is also available. To view all options, look in the json files under `/data/json`
- `tick_marks`: Similar to `properties.HighLights`, it is a list of significant events. Each entry has two fields: `description` which explains what happened ("Team0Save", "Team1Goal") and `frame` which records the frame at which the event occured. Main difference from `properties.HighLights` is that these are simpler and more understandable

### 2. Dynamic Network Frames

This is where physics and gameplay data reside.

#### **Object Dictionary**

- Two registries: `objects` and `names`
- `objects` is a global registry, while `names` is an entity registry. `objects` tells you what kind of thing something is (e.g., a car) while `names` identifies the specific instances of those objects.
- This is useful, as instead of repeating long strings, network frames refer to these by their `object_id` (their index in the `objects` array)

#### **Network Frames**

Located under `network_frames.frames`, this array contains frame-by-frame data about the game. \
Each frame objects stores the following information:

- `time`: the time in seconds into the match
- `delta`: the duration in seconds since the last frame
- `new_actors`: a list of entities that were created (generally empty except for the first frame when everything is initialized)
- `deleted_actors`: a list of entities that were removed. Generally empty
- `updated_actors`: a list of entities that were updated. Each entity has the following fields:
  - `actor_id`/`stream_id`/`object_id`: identifiers of the object being updated
  - `attribute`: the attribute being updated.
  - Example entity:
  ```
  {
    "actor_id": 11,
    "stream_id": 42,
    "object_id": 263,
    "attribute": {
      "RigidBody": {
        "sleeping": false,
        "location": {
          "x": -731.15,
          "y": -61.22,
          "z": 96.15
        },
        "rotation": {
          "x": 0.09977449,
          "y": 0.004124322,
          "z": 0.83124083,
          "w": -0.54686993
        },
        "linear_velocity": {
          "x": -1916.2,
          "y": -253.51,
          "z": 2.43
        },
        "angular_velocity": {
          "x": -62.49,
          "y": -131.85,
          "z": -570.49
        }
      }
    }
  },
  ```
