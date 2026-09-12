from typing import Any, Dict, List


def build_event_metadata(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build the static event stream, using tick-mark frames for goals."""
    goals = data.get("properties", {}).get("Goals", [])
    goal_index = 0
    events: List[Dict[str, Any]] = []

    for tick_mark in data.get("tick_marks", []):
        description = tick_mark.get("description", "")
        tick_frame = tick_mark.get("frame")
        if "Goal" in description and goal_index < len(goals):
            goal = goals[goal_index]
            goal_index += 1
            events.append(
                {
                    "type": "goal",
                    "frame": tick_frame,
                    "description": description,
                    "player_name": goal.get("PlayerName"),
                    "team": goal.get("PlayerTeam"),
                    "metadata_frame": goal.get("frame"),
                }
            )
        else:
            events.append(
                {
                    "type": "tick_mark",
                    "frame": tick_frame,
                    "description": description,
                }
            )

    for goal in goals[goal_index:]:
        events.append(
            {
                "type": "goal",
                "frame": goal.get("frame"),
                "player_name": goal.get("PlayerName"),
                "team": goal.get("PlayerTeam"),
                "metadata_frame": goal.get("frame"),
            }
        )

    return events


def add_reset_event(
    events: List[Dict[str, Any]],
    frame_index: int,
    time: float,
    game_time: float,
    deleted_actor_count: int,
) -> None:
    events.append(
        {
            "type": "reset",
            "frame": frame_index,
            "time": time,
            "game_time": game_time,
            "deleted_actor_count": deleted_actor_count,
        }
    )


def add_demo_event(
    events: List[Dict[str, Any]],
    frame_index: int,
    time: float,
    game_time: float,
    attacker_pri_id: int,
    attacker_name: str,
    victim_car_id: int,
    victim_pri_id: Any,
    victim_name: Any,
) -> None:
    events.append(
        {
            "type": "demo",
            "frame": frame_index,
            "time": time,
            "game_time": game_time,
            "attacker_pri_id": attacker_pri_id,
            "attacker_name": attacker_name,
            "victim_car_id": victim_car_id,
            "victim_pri_id": victim_pri_id,
            "victim_name": victim_name,
        }
    )
