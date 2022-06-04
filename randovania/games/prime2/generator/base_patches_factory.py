import copy
import dataclasses
from random import Random
from typing import Iterator

from randovania.game_description.assignment import NodeConfigurationAssociation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import (PrimeTrilogyBasePatchesFactory, MissingRng)
from randovania.layout.base.base_configuration import BaseConfiguration


class EchoesBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    def create_base_patches(self,
                            configuration: BaseConfiguration,
                            rng: Random,
                            game: GameDescription,
                            is_multiworld: bool,
                            player_index: int,
                            rng_required: bool = True
                            ) -> GamePatches:
        assert isinstance(configuration, EchoesConfiguration)
        parent = super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)

        power_weak = game.dock_weakness_database.get_by_weakness("door", "Permanently Locked")

        def dock(w, a, n):
            return game.world_list.typed_node_by_identifier(NodeIdentifier.create(w, a, n), DockNode)

        return parent.assign_dock_weakness([
            (dock("Temple Grounds", "Service Access", "Door to Meeting Grounds"), power_weak),
            (dock("Temple Grounds", "Agon Transport Access", "Door to Transport to Agon Wastes"), power_weak),
            (dock("Temple Grounds", "Temple Assembly Site", "Door to Temple Transport B"), power_weak),
            (dock("Temple Grounds", "Fortress Transport Access", "Door to Transport to Sanctuary Fortress"), power_weak),
            (dock("Temple Grounds", "Windchamber Tunnel", "Door to Grand Windchamber"), power_weak),
            (dock("Great Temple", "Transport C Access", "Door to Temple Transport C"), power_weak),
        ])

    def configurable_node_assignment(self, configuration: EchoesConfiguration, game: GameDescription,
                                     rng: Random) -> Iterator[NodeConfigurationAssociation]:
        """
        :param configuration:
        :param game:
        :param rng:
        :return:
        """

        all_choices = list(LayoutTranslatorRequirement)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM_WITH_REMOVED)
        without_removed = copy.copy(all_choices)
        without_removed.remove(LayoutTranslatorRequirement.REMOVED)
        random_requirements = {LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED}

        result = []

        scan_visor = search.find_resource_info_with_long_name(
            game.resource_database.item,
            "Scan Visor"
        )
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        for node in game.world_list.iterate_nodes():
            if not isinstance(node, ConfigurableNode):
                continue

            identifier = game.world_list.identifier_for_node(node)
            requirement = configuration.translator_configuration.translator_requirement[identifier]
            if requirement in random_requirements:
                if rng is None:
                    raise MissingRng("Translator")
                requirement = rng.choice(all_choices if requirement == LayoutTranslatorRequirement.RANDOM_WITH_REMOVED
                                         else without_removed)

            translator = game.resource_database.get_by_type_and_index(ResourceType.ITEM, requirement.item_name)
            result.append((identifier, RequirementAnd([
                scan_visor_req,
                ResourceRequirement.simple(translator),
            ])))

        return result
