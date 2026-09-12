from typing import Any, Dict

from src.domain.models import ActorObservation


def is_useful_observation(attribute_name: str, attributes: Dict[str, Any]) -> bool:
    return (
        "RigidBody" in attributes
        or "ReplicatedBoost" in attributes
        or attribute_name == "TAGame.CarComponent_Dodge_TA:DodgeTorque"
    )


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
