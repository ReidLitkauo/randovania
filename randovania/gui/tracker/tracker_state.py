import dataclasses

from randovania.game_description.world.node import Node
from randovania.resolver.state import State


@dataclasses.dataclass(frozen=True)
class TrackerState:
    state: State
    nodes_in_reach: set[Node]
    actions: tuple[Node, ...]
