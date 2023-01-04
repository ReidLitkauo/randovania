
import dataclasses
from random import Random
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.generator import reach_lib
from randovania.generator.item_pool import pool_creator
from randovania.generator.path_generator_reach import PathGeneratorReach
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.preset import Preset


def run_bootstrap(preset: Preset):
    game = filtered_database.game_description_for_layout(preset.configuration).get_mutable()
    generator = game.game.generator

    game.resource_database = generator.bootstrap.patch_resource_database(game.resource_database,
                                                                         preset.configuration)
    permalink = GeneratorParameters(
        seed_number=15000,
        spoiler=True,
        presets=[preset],
    )
    rng = Random(15000)
    patches = generator.base_patches_factory.create_base_patches(preset.configuration, rng,
                                                                 game, False, player_index=0)
    pool_results = pool_creator.calculate_pool_results(preset.configuration,
                                                       game,
                                                       patches,
                                                       rng,
                                                       rng_required=True)
    patches = patches.assign_extra_initial_items(
        pool_results.initial_resources.as_resource_gain()
    )

    _, state = generator.bootstrap.logic_bootstrap(preset.configuration, game, patches)

    return game, state, permalink


def preset_starting_at(base_preset: Preset, identifier: AreaIdentifier) -> Preset:
    return dataclasses.replace(
        base_preset,
        configuration=dataclasses.replace(
            base_preset.configuration,
            starting_location=StartingLocationList.with_elements(
                [identifier],
                base_preset.game,
            ),
        ),
    )


def test_trooper_security_station(default_echoes_preset):
    game, state, _ = run_bootstrap(preset_starting_at(
        default_echoes_preset,
        AreaIdentifier("Temple Grounds", "Trooper Security Station"),
    ))

    reach = PathGeneratorReach(game, state)
    reach._explore()

    resource_nodes = reach_lib.get_collectable_resource_nodes_of_reach(reach)
    assert resource_nodes == [
        game.world_list.node_by_identifier(
            NodeIdentifier.create("Temple Grounds", "Trooper Security Station", "Event - Trooper Security Station Gate")
        )
    ]

def test_trooper_security_station_into_gfmc(default_echoes_preset):
    game, state, _ = run_bootstrap(preset_starting_at(
        default_echoes_preset,
        AreaIdentifier("Temple Grounds", "Trooper Security Station"),
    ))

    reach = PathGeneratorReach(game, state)
    reach._explore()

    resource_nodes = reach_lib.get_collectable_resource_nodes_of_reach(reach)
    assert len(resource_nodes) == 1
    reach.act_on(resource_nodes[0])

    for n in reach.nodes:
        print(game.world_list.node_name(n), reach.is_reachable_node(n))

    assert False
