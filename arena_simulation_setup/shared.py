import typing

import attrs
from arena_simulation_setup.entities.obstacles.dynamic import \
    loader as DynamicObstacleLoader
from arena_simulation_setup.entities.obstacles.static import \
    loader as ObstacleLoader
from arena_simulation_setup.entities.robot import loader as RobotLoader
from arena_simulation_setup.utils.models import ModelWrapper
from arena_simulation_setup.utils.models.model_loader import ModelLoader

from .utils.geometry import Position, PositionOrientation, PositionRadius


def override_or_parse(parser: ModelLoader) -> typing.Callable[[typing.Any], ModelWrapper]:
    def validator(v: typing.Any) -> ModelWrapper:
        if isinstance(v, ModelWrapper):
            return parser.bind(v.name)
        return parser.bind(v)
    return validator


@attrs.frozen()
class Wall:
    Start: Position
    End: Position
    height: float = attrs.field(converter=float, default=2.)
    texture_material: str = ''  # not implemented

    @classmethod
    def parse(cls, obj: list) -> "Wall":
        kwargs = {}
        if len(obj) > 2 and isinstance(obj[2], dict):
            kwargs = obj[2]
        return cls(
            **kwargs,
            Start=Position(x=obj[0][0], y=obj[0][1]),
            End=Position(x=obj[1][0], y=obj[1][1]),
        )


@attrs.frozen()
class Entity:
    position: PositionOrientation
    name: str
    model: ModelWrapper
    extra: dict = attrs.field(factory=dict, kw_only=True)

    def asdict(self, expand_extra: bool = True) -> dict:
        if expand_extra:
            return {
                **attrs.asdict(self, filter=lambda a, v: a.name != 'extra'),
                **self.extra,
            }
        return attrs.asdict(self)


@attrs.frozen()
class Obstacle(Entity):
    model: ModelWrapper = attrs.field(converter=override_or_parse(ObstacleLoader))

    @classmethod
    def parse(cls, obj: dict) -> "Obstacle":
        name = str(obj.get("name", ""))
        position = PositionOrientation(*obj.get("pos", (0, 0, 0)))
        model = str(obj.get("model", ""))

        return cls(
            name=name,
            position=position,
            model=model,
            extra=obj,
        )


@attrs.frozen()
class DynamicObstacle(Obstacle):
    model: ModelWrapper = attrs.field(converter=override_or_parse(DynamicObstacleLoader))
    waypoints: list[PositionRadius]

    @classmethod
    def parse(cls, obj: dict) -> "DynamicObstacle":

        base = Obstacle.parse(obj)
        waypoints = [
            PositionRadius(*waypoint)
            for waypoint
            in obj.get("waypoints", [])
        ]

        return cls(
            **attrs.asdict(base, recurse=False),
            waypoints=waypoints,
        )


@attrs.frozen()
class Robot(Entity):
    model: ModelWrapper = attrs.field(converter=override_or_parse(RobotLoader))
