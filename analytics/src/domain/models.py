from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ActorObservation:
    """Useful actor data retained until its network links can be resolved."""

    frame: int
    time: float
    delta: float
    game_time: float
    actor_id: int
    attribute_name: str
    attributes: Dict[str, Any]
