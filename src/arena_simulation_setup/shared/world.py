from __future__ import annotations

import typing

import attrs

from arena_simulation_setup.utils.cattrs import (
    register_parse,
)

from arena_simulation_setup.utils.geometry import Pose, Position
from arena_simulation_setup.entities.materials import Material, FloorMaterialLoader


@register_parse
@attrs.define
class Elevator:
    name: str
    position: list[float]
    size: list[float] = attrs.field(factory=lambda: [2.0, 2.0, 0.2])
    height_min: float = 0.0
    height_max: float = 3.0
    material: str = "Metal"  # TODO
    destination: str = attrs.field(default="")


@register_parse
@attrs.define
class Door:
    name: str
    start: Position = attrs.field(converter=Position.converter)
    end: Position = attrs.field(converter=Position.converter)
    kind: typing.Literal['sliding'] = 'sliding'
    pose: Pose = attrs.field(factory=Pose, converter=Pose.converter)
    description: str = attrs.field(default="")
    height: float = attrs.field(default=2.0)
    material: str = attrs.field(default="Adobe_Bricks_01")  # TODO


@attrs.define
class Floor:
    pos: Position = attrs.field(converter=Position.converter)
    x_length: float = attrs.field(converter=float, default=20.)
    y_length: float = attrs.field(converter=float, default=20.)
    mat: Material = attrs.field(converter=FloorMaterialLoader, default=Material.DEFAULT)
