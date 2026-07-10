# rrrocket JSON Output Structure

This file outlines how the json files output by rrrocket are parsed. These files are under the path ./data/json

## Overview

[rrrocket](https://github.com/nickbabcock/rrrocket) parses a binary `.replay` files into a readable json format. The data is partitioned into two distinct categories: Static Metadata (game properties) and Dynamic Network Frames (frame-by-frame state).

### 1. Static Metadata

Located at the root of the JSON object, this contains useful metadata on the game

- `properties`:
  - `TeamSize`: Size of each team (1, 2, 3)
  - `Team0Score`/`Team1Score`: The final score for each team (0 = blue, 1 = orange)
  - `TotalSecondsPlayed`: The length of the match (300 seconds + overtime)
  - `Goals`: A list of goal events, with each event having the `frame` at which the goal occured, the `PlayerName` of who scored the goal, and the `PlayerTeam` who scored
  - `Highlights`: A list of signifigant events in the game. Each event has a `frame` at which it occured, a `CarName` and `BallName` of the internal names of the objects involved, and a `GoalActorName` that is a flag that determines if a goal was scored.
