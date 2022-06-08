from __future__ import annotations

import copy
import dataclasses
import typing
from dataclasses import dataclass
from typing import Iterator, Optional

from randovania.game_description.resources.resource_info import ResourceCollection, ResourceGain
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier

ElevatorConnection = dict[NodeIdentifier, AreaIdentifier]

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.world.dock import DockWeakness
    from randovania.game_description.assignment import (
        PickupTarget, PickupTargetAssociation, TeleporterAssociation,
        NodeConfigurationAssociation, DockWeaknessAssociation
    )
    from randovania.game_description.hint import Hint
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.game_description.world.node import Node
    from randovania.game_description.world.teleporter_node import TeleporterNode
    from randovania.game_description.world.dock_node import DockNode


@dataclass(frozen=True)
class GamePatches:
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """
    game: GameDescription
    player_index: int
    configuration: BaseConfiguration
    pickup_assignment: dict[PickupIndex, PickupTarget]
    elevator_connection: ElevatorConnection
    dock_connection: dict[NodeIdentifier, NodeIdentifier]
    dock_weakness: list[Optional[DockWeakness]]
    configurable_nodes: dict[NodeIdentifier, Requirement]
    starting_items: ResourceCollection
    starting_location: AreaIdentifier
    hints: dict[NodeIdentifier, Hint]

    def __post_init__(self):
        from randovania.game_description.resources.resource_info import ResourceCollection
        if not isinstance(self.starting_items, ResourceCollection):
            raise TypeError("starting_items must be a ResourceCollection")

        for resource, _ in self.starting_items.as_resource_gain():
            if resource.resource_type != ResourceType.ITEM:
                raise ValueError(f"starting_items must have only Items, not {resource}")

    @classmethod
    def create_from_game(cls, game: GameDescription, player_index: int, configuration: BaseConfiguration,
                         ) -> GamePatches:
        game.world_list.ensure_has_node_cache()
        return GamePatches(
            game, player_index, configuration, {}, game.get_default_elevator_connection(),
            {}, [None] * len(game.world_list.all_nodes), {},
            ResourceCollection.with_database(game.resource_database),
            game.starting_location, {},
        )

    def assign_new_pickups(self, assignments: Iterator[PickupTargetAssociation]) -> GamePatches:
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            new_pickup_assignment[index] = pickup

        return dataclasses.replace(self, pickup_assignment=new_pickup_assignment)

    def assign_node_configuration(self, assignment: Iterator[NodeConfigurationAssociation]) -> "GamePatches":
        new_configurable = copy.copy(self.configurable_nodes)

        for identifier, requirement in assignment:
            assert identifier not in new_configurable
            new_configurable[identifier] = requirement

        return dataclasses.replace(self, configurable_nodes=new_configurable)

    def assign_starting_location(self, location: AreaIdentifier) -> "GamePatches":
        return dataclasses.replace(self, starting_location=location)

    def assign_extra_initial_items(self, new_resources: ResourceGain) -> "GamePatches":
        current = self.starting_items.duplicate()
        current.add_resource_gain(new_resources)
        return dataclasses.replace(self, starting_items=current)

    def assign_hint(self, identifier: NodeIdentifier, hint: Hint) -> "GamePatches":
        current = copy.copy(self.hints)
        current[identifier] = hint
        return dataclasses.replace(self, hints=current)

    # Elevators
    def assign_elevators(self, assignments: Iterator[TeleporterAssociation]) -> GamePatches:
        elevator_connection = copy.copy(self.elevator_connection)

        for teleporter, target in assignments:
            elevator_connection[teleporter.identifier] = target

        return dataclasses.replace(self, elevator_connection=elevator_connection)

    def get_elevator_connection_for(self, node: TeleporterNode) -> Optional[AreaIdentifier]:
        return self.elevator_connection.get(node.identifier, node.default_connection)

    def all_elevator_connections(self) -> Iterator[TeleporterAssociation]:
        for identifier, target in self.elevator_connection.items():
            yield self.game.world_list.get_teleporter_node(identifier), target

    # Dock Connection
    def assign_dock_connections(self, assignment: Iterator[DockNode, Node]) -> GamePatches:
        connections = copy.copy(self.dock_connection)

        for source, target in assignment:
            connections[source] = target

        return dataclasses.replace(self, dock_connection=connections)

    def get_dock_connection_for(self, node: DockNode) -> Node:
        target_identifier = self.dock_connection.get(node.identifier, node.default_connection)
        return self.game.world_list.node_by_identifier(target_identifier)

    def all_dock_connections(self) -> Iterator[tuple[NodeIdentifier, NodeIdentifier]]:
        yield from self.dock_connection.items()

    # Dock Weakness
    def assign_dock_weakness(self, weaknesses: Iterator[tuple[DockNode, DockWeakness]]) -> "GamePatches":
        new_weakness = list(self.dock_weakness)

        for node, weakness in weaknesses:
            new_weakness[node.get_index()] = weakness

        return dataclasses.replace(self, dock_weakness=new_weakness)

    def get_dock_weakness_for(self, node: DockNode) -> DockWeakness:
        return self.dock_weakness[node.get_index()] or node.default_dock_weakness

    def all_dock_weaknesses(self) -> Iterator[DockWeaknessAssociation]:
        nodes = self.game.world_list.all_nodes
        for index, weakness in enumerate(self.dock_weakness):
            if weakness is not None and (node := nodes[index]) is not None:
                yield node, weakness
