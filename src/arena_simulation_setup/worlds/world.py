import os
import typing

import attrs
import yaml

from arena_simulation_setup import ProviderBase, SourcesContainer, ass_sources
from arena_simulation_setup.entities.materials import (
    FloorMaterialLoader,
    MaterialProvider,
)
from arena_simulation_setup.shared import Door, DynamicObstacle, Floor, Obstacle, Wall
from arena_simulation_setup.utils.cattrs import converter
from arena_simulation_setup.utils.geometry import Position

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
            dynamic: list[DynamicObstacle] = attrs.field(factory=list)

        name: str
        corners: list[Position] = attrs.field(factory=list)
        walls: list[Wall] = attrs.field(factory=list)
        doors: list[Door] = attrs.field(factory=list)
        material: MaterialProvider = attrs.field(converter=FloorMaterialLoader, factory=FloorMaterialLoader.DEFAULT)
        entities: WorldEntities = attrs.field(factory=WorldEntities)
        description: str = ''

        @property
        def floor(self) -> Floor:
            x_min = min(corner.x for corner in self.corners)
            y_min = min(corner.y for corner in self.corners)
            x_max = max(corner.x for corner in self.corners)
            y_max = max(corner.y for corner in self.corners)
            pos = Position(x=(x_min + x_max) / 2, y=(y_min + y_max) / 2)
            x_length = x_max - x_min
            y_length = y_max - y_min
            return Floor(pos=pos, x_length=x_length, y_length=y_length, material=self.material)

    zones: list[Zone] = attrs.field(factory=list)

    @property
    def all_walls(self) -> typing.Iterable[Wall]:
        return (wall for zone in self.zones for wall in zone.walls)

    @property
    def all_doors(self) -> typing.Iterable[Door]:
        return (door for zone in self.zones for door in zone.doors)

    @property
    def all_floors(self) -> typing.Iterable[Floor]:
        return (zone.floor for zone in self.zones)

    @property
    def all_static_entities(self) -> typing.Iterable[Obstacle]:
        return (entity for zone in self.zones for entity in zone.entities.static)

    @property
    def all_dynamic_entities(self) -> typing.Iterable[Obstacle]:
        return (entity for zone in self.zones for entity in zone.entities.dynamic)


class WorldProvider(ProviderBase):

    @classmethod
    def list(cls):
        return ('.generated', *super().list())

    @classmethod
    def resolve(cls, path: str) -> str:
        return os.path.join(cls._sources.global_dir, path)

    @property
    def scenario(self):
        return ScenarioProvider.bind(ass_sources.override(**{SourcesContainer.Keys.WORLD.value: self.path})('scenarios'))

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


World = WorldProvider.bind(ass_sources('worlds'))
