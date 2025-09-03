from __future__ import annotations

import abc
import itertools
import math
import os
import typing
from collections.abc import Iterable

import attrs
import yaml

from arena_simulation_setup import ProviderBase, ass_dir
from arena_simulation_setup.entities.materials import Material, WallMaterialLoader
from arena_simulation_setup.entities.obstacles.static import (
    loader as ObstacleModelLoader,
)
from arena_simulation_setup.shared.entities import Obstacle
from arena_simulation_setup.utils.cattrs import Parseable, converter, register_parse
from arena_simulation_setup.utils.geometry import Orientation, Pose, Position
from arena_simulation_setup.utils.models import Model

###
# Parsing wall description
###


@register_parse
class PositionalNumber(Parseable):
    def __init__(self, *, absolute: typing.Optional[float] = None, relative: typing.Optional[float] = None):
        if absolute is not None:
            self._absolute = absolute
            self._relative = None
        elif relative is not None:
            self._absolute = None
            self._relative = relative
        else:
            raise ValueError("Must specify either absolute or relative.")

    def absolute(self, low: float, high: float) -> float:
        if self._absolute is not None:
            if math.copysign(1, self._absolute) < 0:
                return high + self._absolute
            return self._absolute
        if self._relative is not None:
            return low + (high - low) * self._relative

    def realize(self, start: Position, end: Position) -> Position:
        line_length = math.dist((start.x, start.y), (end.x, end.y))
        return start + self.absolute(0.0, line_length) * (end - start)

    @classmethod
    def parse(cls, value: typing.Any) -> PositionalNumber:
        if isinstance(value, str) and value.endswith('%'):
            return cls(relative=float(value[:-1]) / 100.0)
        return cls(absolute=float(value))


@attrs.define(kw_only=True)
class SubWall(abc.ABC):
    x: float = attrs.field(converter=float, default=0.0)  # x axis shift [m]
    y: float = attrs.field(converter=float, default=0.0)  # y axis shift [m]
    z: float = attrs.field(converter=float, default=0.0)  # z axis shift [m]

    def _shift(self, pos: Position) -> Position:
        return Position(
            x=pos.x + self.x,
            y=pos.y + self.y,
            z=pos.z + self.z,
        )

    @abc.abstractmethod
    def realize(self, start: Position, end: Position) -> WallRealization:
        pass


@attrs.define(kw_only=True)
class TilingAsset(SubWall):
    """
    Place repeating asset along the wall.
    """
    tile: list[SubWallT]  # sub-assets to place
    every: float  # place every N meters

    def realize(self, start: Position, end: Position) -> WallRealization:
        start = self._shift(start)
        end = self._shift(end)

        r_walls, r_obstacles = itertools.chain(()), itertools.chain(())
        within = (end - start).norm()

        i = 0
        while (p := i * self.every) < within:
            for asset in self.tile:
                walls, obstacles = asset.realize(start + p * (end - start), start + (p + self.every) * (end - start))
                r_walls = itertools.chain(r_walls, walls)
                r_obstacles = itertools.chain(r_obstacles, obstacles)
            i += 1
        return (r_walls, r_obstacles)


@attrs.define(kw_only=True)
class FillAsset(SubWall):
    """
    Place along slice of the wall.
    """
    fill: list[SubWallT]
    start: PositionalNumber = PositionalNumber.parse(0.0)  # start at N meters along the wall
    end: PositionalNumber = PositionalNumber.parse(-0.0)  # end at N meters along the wall

    def realize(self, start: Position, end: Position) -> WallRealization:
        start = self._shift(start)
        end = self._shift(end)

        r_start = self.start.realize(start, end)
        r_end = self.end.realize(start, end)

        return (e.realize(r_start, r_end) for e in self.fill) | itertools.chain(())


@attrs.define(kw_only=True)
class PlaceObstacleAsset(SubWall):
    """
    Place a single obstacle.
    """
    x: PositionalNumber = PositionalNumber.parse(0.0)  # x axis shift [m]
    y: PositionalNumber = PositionalNumber.parse(0.0)  # y axis shift [m]
    z: PositionalNumber = PositionalNumber.parse(0.0)  # z axis shift [m]

    model: str
    name: str = ""
    orientation: Orientation = attrs.field(factory=Orientation.identity)

    def realize(self, start: Position, end: Position) -> WallRealization:
        start = Position(
            x=self.x.realize(start, end).x,
            y=self.y.realize(start, end).y,
            z=self.z.realize(start, end).z,
        )
        end = Position(
            x=self.x.realize(start, end).x,
            y=self.y.realize(start, end).y,
            z=self.z.realize(start, end).z,
        )

        return (), (
            Obstacle(
                name=self.name or self.model,
                model=self.model,
                pose=Pose(
                    position=Position(
                        x=self.x.realize(start, end).x,
                        y=self.y.realize(start, end).y,
                        z=self.z.realize(start, end).z,
                    ),
                    orientation=self.orientation * (end - start).to_orientation(),
                ),
            ),
        )


@attrs.define(kw_only=True)
class PlaceWallSegmentAsset(SubWall):
    """
    Place a single wall segment.
    """
    material: str
    height: float = attrs.field(converter=float, default=2.0)
    width: float = attrs.field(converter=float, default=0.05)
    name: str = ""

    def realize(self, start: Position, end: Position) -> WallRealization:
        start = self._shift(start)
        end = self._shift(end)

        return (
            WallSegment(
                start=start,
                end=end,
                height=self.height,
                width=self.width,
                material=WallMaterialLoader(self.material),
            ),
        ), ()


SubWallT = TilingAsset | FillAsset | PlaceObstacleAsset | PlaceWallSegmentAsset


###
# Realization of a wall description
###


@attrs.define
class WallSegment:
    start: Position
    end: Position
    height: float
    width: float
    material: Material


WallRealization = tuple[Iterable[WallSegment], Iterable[Obstacle]]


@attrs.define
class WallDescription:
    main: list[SubWallT]

    def realize(self, start: Position, end: Position) -> WallRealization:
        r_walls, r_obstacles = itertools.chain(()), itertools.chain(())
        for subwall in self.main:
            walls, obstacles = subwall.realize(start, end)
            r_walls = itertools.chain(r_walls, walls)
            r_obstacles = itertools.chain(r_obstacles, obstacles)

        return (r_walls, r_obstacles)

    @classmethod
    def simple(cls, material: typing.Optional[Material] = None) -> WallDescription:
        if material is None:
            material = Material.DEFAULT
        return cls(
            main=[
                PlaceWallSegmentAsset(
                    material=material
                )
            ]
        )


class WallProvider(ProviderBase):
    def load(self) -> WallDescription:
        with open(self.path) as f:
            return converter.structure(yaml.safe_load(f), WallDescription)


loader = WallProvider.bind(os.path.join(ass_dir, 'entities', 'walls'))
