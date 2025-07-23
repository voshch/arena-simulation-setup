import re
import typing

import attrs

from arena_simulation_setup.entities.obstacles.dynamic import \
    loader as DynamicObstacleLoader
from arena_simulation_setup.entities.obstacles.static import \
    loader as ObstacleLoader
from arena_simulation_setup.entities.robot import loader as RobotLoader
from arena_simulation_setup.utils.cattrs import Parseable, register_parse
from arena_simulation_setup.utils.models import ModelWrapper
from arena_simulation_setup.utils.models.model_loader import ModelLoader

from .utils.geometry import *


def model_parse(parser: ModelLoader, *, overrides: typing.Iterable[ModelLoader] = ()) -> typing.Callable[[typing.Any], ModelWrapper]:
    def validator(v: str | ModelWrapper) -> ModelWrapper:
        if isinstance(v, ModelWrapper):
            if any(v.loader_matches(overridee) for overridee in overrides):
                return parser.bind(v.name)
            return v
        return parser.bind(v)
    return validator


@register_parse
@attrs.define
class Wall(Parseable):
    start: Position
    end: Position
    height: float = attrs.field(converter=float, default=2.)
    mat: str = ''  # wall material

    @classmethod
    def parse(cls, value: list | dict) -> "Wall":
        if isinstance(value, list):
            kwargs = {}
            if len(value) == 3 and isinstance(value[2], dict):
                kwargs = value[2]
            return cls(
                **kwargs,
                start=Position(x=value[0][0], y=value[0][1]),
                end=Position(x=value[1][0], y=value[1][1]),
            )
        elif isinstance(value, dict):
            return cls(**value)
        else:
            raise ValueError(f"Could not parse as wall: {value}")


@attrs.define
class Entity:
    pose: Pose
    name: str = attrs.field(converter=lambda s: Entity.sanitize_name(str(s)))
    model: ModelWrapper
    extra: dict = attrs.field(factory=dict, kw_only=True)

    def asdict(self, expand_extra: bool = True) -> dict:
        if expand_extra:
            return {
                **attrs.asdict(self, filter=lambda a, v: a.name != 'extra'),
                **self.extra,
            }
        return attrs.asdict(self)

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        return re.sub('[^A-Za-z0-9_]', '_', name)


@attrs.define
class Obstacle(Entity):
    model: ModelWrapper = attrs.field(converter=model_parse(ObstacleLoader))


@attrs.define
class DynamicObstacle(Obstacle):
    model: ModelWrapper = attrs.field(converter=model_parse(DynamicObstacleLoader, overrides=(ObstacleLoader,)))
    waypoints: list[Position]


@attrs.define
class Robot(Entity):
    model: ModelWrapper = attrs.field(converter=model_parse(RobotLoader))
