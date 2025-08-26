import re
import typing

import attrs

from arena_simulation_setup.entities.obstacles.dynamic import \
    loader as DynamicObstacleLoader
from arena_simulation_setup.entities.obstacles.static import \
    loader as ObstacleLoader
from arena_simulation_setup.entities.robot import loader as RobotLoader
from arena_simulation_setup.utils.cattrs import Parseable, converter, register_parse
from arena_simulation_setup.utils.models import ModelWrapper
from arena_simulation_setup.utils.models.model_loader import ModelLoader

from .utils.geometry import *
import warnings


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


@register_parse
@attrs.define
class Door:
    """
    Description of a door
    """
    name: str
    start: Position
    end: Position
    kind: typing.Literal['sliding'] = 'sliding'
    pose: Pose = attrs.field(factory=Pose)
    description: str = attrs.field(default="")
    height: float = attrs.field(default=2.0)
    material: str = attrs.field(default="Adobe_Bricks_01")


@register_parse
@attrs.define
class Floor(Parseable):
    pos: Position
    x_length: float = attrs.field(converter=float, default=20.)
    y_length: float = attrs.field(converter=float, default=20.)
    mat: str = ''  # wall material

    @classmethod
    def parse(cls, value: list | dict) -> "Floor":
        if isinstance(value, list):
            kwargs = {}
            if len(value) == 3 and isinstance(value[0], dict):
                kwargs = value[0]
            return cls(
                **kwargs,
                pos=Position(x=value[1][0], y=value[1][1]),
                x_length=value[2],
                y_length=value[3],
            )
        elif isinstance(value, dict):
            return cls(**value)
        else:
            raise ValueError(f"Could not parse as floor: {value}")


EntityT = typing.TypeVar("EntityT", bound="Entity")


@attrs.define
class Entity(Parseable):
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

    @classmethod
    def parse(cls: typing.Type[EntityT], value: dict) -> EntityT:
        warnings.warn(
            "Entity.parse is deprecated and will be removed in a future release. "
            "Call the constructor directly, e.g., Entity(**value).",
            FutureWarning,
            stacklevel=2
        )
        if 'pos' in value:
            value['pose'] = value['pos']
            del value['pos']
        return converter.structure(value, cls)


@attrs.define
class Obstacle(Entity):
    model: ModelWrapper = attrs.field(converter=model_parse(ObstacleLoader))


@attrs.define
class DynamicObstacle(Obstacle):
    model: ModelWrapper = attrs.field(converter=model_parse(DynamicObstacleLoader, overrides=(ObstacleLoader,)))
    waypoints: list[Position]
    velocity: float = attrs.field(converter=float, default=1.0)  # m/s


@attrs.define
class CustomDynamicObstacle(DynamicObstacle):
    """
    DynamicObstacles but with properties can be define in runtime
    """

    def __getattr__(self, name):
        """
        Allow access to dynamic attributes "attr_name" via self.attr_name
        """
        if name in self.extra:
            return self.extra[name]
        raise AttributeError(f"{name} not found")

    @classmethod
    def parse(cls, value) -> "CustomDynamicObstacle":
        known_fields = set(f.name for f in attrs.fields(cls))

        if 'pos' in value:
            value['pose'] = value['pos']
            del value['pos']

        known_values = {k: v for k, v in value.items() if k in known_fields}
        custom_fields = {k: v for k, v in value.items() if k not in known_fields}

        warnings.warn(
            "CustomDynamicObstacle.parse is deprecated and will be removed in a future release. "
            "Call the constructor directly, e.g., CustomDynamicObstacle(**value).",
            FutureWarning,
            stacklevel=2
        )

        obj = cls(**known_values)
        obj.extra.update(custom_fields)
        value = obj.asdict(True)

        return converter.structure(value, cls)


@attrs.define
class Robot(Entity):
    model: ModelWrapper = attrs.field(converter=model_parse(RobotLoader))
