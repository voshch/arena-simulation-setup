import os
import typing

import attrs
import yaml

from arena_simulation_setup import ProviderBase, ass_dir
from arena_simulation_setup.shared import Obstacle, Wall, Door
from arena_simulation_setup.utils.geometry import Position
from arena_simulation_setup.utils.cattrs import converter

from .map import Map
from .scenario import ScenarioProvider


@attrs.define
class WorldDescription:
    """
    Description of the 3D world
    """

    @attrs.define
    class Zone:
        """
        Description of a zone (e.g. room) within the 3D world
        """

        @attrs.define
        class WorldEntities:
            """
            Description of the entities within the 3D world
            """
            static: list[Obstacle] = attrs.field(factory=list)
            dynamic: list[Obstacle] = attrs.field(factory=list)

        name: str
        corners: list[Position] = attrs.field(factory=list)
        walls: list[Wall] = attrs.field(factory=list)
        doors: list[Door] = attrs.field(factory=list)
        mat: str = attrs.field(default="")  # floor material
        entities: WorldEntities = attrs.field(factory=WorldEntities)
        description: str = attrs.field(default="")

    zones: list[Zone] = attrs.field(factory=list)

    @property
    def all_walls(self) -> typing.Iterable[Wall]:
        return (wall for zone in self.zones for wall in zone.walls)

    @property
    def all_doors(self) -> typing.Iterable[Door]:
        return (door for zone in self.zones for door in zone.doors)

    @property
    def all_static_entities(self) -> typing.Iterable[Obstacle]:
        return (entity for zone in self.zones for entity in zone.entities.static)

    @property
    def all_dynamic_entities(self) -> typing.Iterable[Obstacle]:
        return (entity for zone in self.zones for entity in zone.entities.dynamic)


class WorldProvider(ProviderBase):

    @classmethod
    def list(cls) -> list[str]:
        return ['.generated'] + super().list()

    @property
    def scenario(self):
        return ScenarioProvider.bind(os.path.join(self.path, 'scenarios'))

    @property
    def map(self):
        return Map(os.path.join(self.path, 'map'))

    @property
    def world_path(self) -> str:
        return os.path.join(self.path, 'world.yaml')

    def load(self) -> WorldDescription:
        with open(self.world_path) as f:
            return converter.structure(
                yaml.safe_load(f),
                WorldDescription
            )


World = WorldProvider.bind(os.path.join(ass_dir, 'worlds'))
