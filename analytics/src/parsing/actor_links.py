from typing import Any, Dict, List, Optional, Tuple

from src.domain.models import ActorObservation


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
