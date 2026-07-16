# rrrocket JSON Output Structure

This file outlines how the json files output by rrrocket are parsed. These files are under the path ./data/json

## Overview

[rrrocket](https://github.com/nickbabcock/rrrocket) parses a binary `.replay` files into a readable json format. The data is partitioned into two distinct categories: Static Metadata (game properties) and Dynamic Network Frames (frame-by-frame state).

## 1. Static Metadata

Located at the root of the JSON object, this contains useful metadata on the game. \
To see all available metadata, its easiest to run:

```bash
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

## 2. Dynamic Network Frames

This is where physics and gameplay data reside.

### **Object Dictionary**

- Two registries: `objects` and `names`
- `objects` is a global registry, while `names` is an entity registry. `objects` tells you what kind of thing something is (e.g., a car) while `names` identifies the specific instances of those objects.
- This is useful, as instead of repeating long strings, network frames refer to these by their `object_id` (their index in the `objects` array)

### **Network Frames**

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
  ```json
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

## 3. Data Entity Mapping

Because Rocket League’s networking code is asynchronous, it doesn't send "Here is Player X driving Car Y" in one clean packet. It sends bits and pieces, and our script has to reconstruct the relationship.

There are three id's necessary for complete linking: The PRI (player id), the pawn (car id), and the component (boost id).

- **The PlayerReplicationInfo (PRI)**: An actor that holds the player's network identity, such as their name, what platform they are on, and their ping.
- **The Pawn**: The actor that actually exists on the field and has physics
- **The Component**: This is a component that holds the player's current boost level

These links are defined in the `updated_objects` array of the first frame. In the following example, we can see how this flow works.

```json
{
  "actor_id": 20, // unique identifier for the object
  "stream_id": 21, // irrelevant network info
  "object_id": 303, // The type of object this is
  "attribute": {
    "ActiveActor": { // link to another actor
      "active": true,
      "actor": 19
    }
  }
},
{
  "actor_id": 21,
  "stream_id": 21,
  "object_id": 303,
  "attribute": {
    "ActiveActor": {
      "active": true,
      "actor": 19
    }
  }
},
```
Above, we can see two actors with id's of 19 and 20 both linked to an actor with an `actor_id` of 19 through the `ActiveActor` field. Both of these have the same object id of 303. Searching up the element at `objects[303]`, we get ***"TAGame.CarComponent_TA:Vehicle"***. \

This may be confusing at first, as how can one actor (in this case a player, which we will see later) have multiple cars? A Vehicle object, however is a umbrella component of a car, which includes many things. If you look further through the JSON, you will find all actor_id's from 20-24 are linked to actor 19. \
If we dig further into some of these id's, we can see something like this: 

```json
{
  "actor_id": 21,
  "name_id": 21,
  "object_id": 333,
  "initial_trajectory": {
    "location": {
      "x": -256,
      "y": 3840,
      "z": 36
    },
    "rotation": null
  }
},
```

This shows actor 21 has an `object_id` of 318, which corresponds to ***Archetypes.CarComponents.CarComponent_Boost***. This means that actor 21 corresponds to boost. Following a similar process for the rest of the actors yeilds these results:
- **Actor 20**: Archetypes.CarComponents.CarComponent_DoubleJump 
- **Actor 21**: Archetypes.CarComponents.CarComponent_Boost
- **Actor 22**: Archetypes.CarComponents.CarComponent_FlipCar
- **Actor 23**: Archetypes.CarComponents.CarComponent_Dodge
- **Actor 24**: Archetypes.CarComponents.CarComponent_Jump

*It is important to note that a player does not have multiple cars; rather, a single Pawn (the car's physics body) acts as a host to multiple Component actors (Boost, Jump, Dodge) which are all registered to the same Pawn host via the ActiveActor field.*

This shows how each component of the car is linked to the actor with id 19. If we continue the trace to `actor_id` 19, we see this:

```json
{
  "actor_id": 19,
  "stream_id": 23,
  "object_id": 242,
  "attribute": {
    "ActiveActor": {
      "active": true,
      "actor": 3
    }
  }
},
{
  "actor_id": 19,
  "stream_id": 42,
  "object_id": 263,
  "attribute": {
    "RigidBody": {
      "sleeping": false,
      "location": {
        "x": -256.0,
        "y": 3840.0,
        "z": 17.01
      },
      "rotation": {
        "x": 0.0033744453,
        "y": 0.0033744453,
        "z": -0.707096,
        "w": 0.70710146
      },
      "linear_velocity": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.27
      },
      "angular_velocity": {
        "x": 0.06,
        "y": 0.0,
        "z": 0.0
      }
    }
  }
},
```

Firstly, we can see that this actor has an `object_id` of 242, which corresponds to ***"Engine.Pawn:PlayerReplicationInfo"***. Therefore, our car component links had an `"actor": 19` field were 1 car being tied to this player. We can also see that there is another `object_id` of 263, which corresponds to ***TAGame.RBActor_TA:ReplicatedRBState***. This links the physics. \

This snippet also links this PRI object to an actor with an `actor_id` of 3. Following this leads to:

```json
{
  "actor_id": 3,
  "stream_id": 34,
  "object_id": 124,
  "attribute": {
    "String": "Baby Sparta"
  }
},
```

Where we can see the actor with the id 3.The `object_id` of 124 identifies this object as *"Engine.PlayerReplicationInfo:PlayerName"*. This is backed up by the attribute field that has the name *Baby Sparta*.

This example showed how linking occurs for the player named *Baby Sparta*. This same process occurs for every other object on the field.

The following diagram illustrates the relationship between a Player's identity, their physics Pawn, and their gameplay components:

```
[ PLAYER IDENTITY (PRI) ]  <-- (ActiveActor Link) -- [ CAR PHYSICS (Pawn) ]
|
|-- (ActiveActor Link) --> [ Boost Component ]
|
|-- (ActiveActor Link) --> [ Jump Component ]
|
|-- (ActiveActor Link) --> [ Dodge Component ]
|
|-- (ActiveActor Link) --> [ Flip Component ]
```

## 4. Pipeline Logic

**_Forward Filling_**: Since rrrocket only logs data when it changes, we need to fill data in with the last known value if there is not a new value for it on a given frame. This ensures that our data is continuous and can be viewed in isolation.

To transform the raw network stream into a structured dataset, our ETL pipeline operates in three distinct phases:

### A. State Accumulation
Because the replay data is delta-encoded, the server only broadcasts an object's properties when they change. Our parser maintains an in-memory State Registry (a dictionary of current actor values). As we iterate through the network_frames.frames array:

- **Update Registry**: When an updated_actor appears, we immediately patch our local dictionary with the new values.

- **Linkage Resolution**: We look for specific attributes (like ActiveActor) to dynamically map Components to Pawns, and Pawns to PRIs.

### B. The "Snapshot" Transformation
While the network data is delta-encoded, our output is Snapshot-based. We don't just output when something changes; we output the current state of every entity for every frame.

If a frame contains no update for the RigidBody of actor_id 19, our parser infers that the position/velocity remains identical to the previous frame and carries that state forward.

### C. Forward Filling (Pandas Normalization)
Finally, we use Pandas to finalize the time-series continuity:

- **ffill() (Forward Fill):** Even with our internal registry, there may be slight gaps in the data. We apply df.ffill() on continuous columns (loc_x, boost_amount, etc.) to ensure that every frame has a valid value, effectively "holding" the last known state until the next update.

- **Dodge State Handling:** Unlike continuous physics data, binary events like is_dodging are momentary. After the forward-fill operation, we explicitly force NaN values in this column to 0 (False). This ensures that a dodge is treated as a discrete event rather than a persistent state.