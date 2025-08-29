import re
import typing
import os 
import yaml
import sys
sys.setrecursionlimit(10000)

import attrs
import numpy as np
import math 

from arena_simulation_setup.entities.obstacles.dynamic import \
    loader as DynamicObstacleLoader
from arena_simulation_setup.entities.obstacles.static import \
    loader as ObstacleLoader
from arena_simulation_setup.entities.robot import loader as RobotLoader
from arena_simulation_setup.utils.cattrs import Parseable, converter, register_parse
from arena_simulation_setup.utils.models import ModelWrapper
from arena_simulation_setup.utils.models.model_loader import ModelLoader
from arena_simulation_setup.utils.cattrs import converter
from arena_simulation_setup import ass_dir
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
class WallAsset:
    kind: str              # "fill" or "tile"
    name: str              # value of the key
    file: str = ""
    every: float = 1.0
    height: float = 0.0
    width: float = 0.0
    x_offset: float = 0.0
    y_offset: float = 0.0
    z_offset: float = 0.0
    material: str = ""
    material_name: str = ""

    @classmethod
    def _structure(cls, obj: dict, _: type) -> "WallAsset":
        if not isinstance(obj, dict):
            raise TypeError(f"WallAsset expects a mapping, got {type(obj)}")

        if "fill" in obj:
            return cls(kind="fill", name=obj["fill"],
                       **{k: v for k, v in obj.items() if k != "fill"})
        if "tile" in obj:
            return cls(kind="tile", name=obj["tile"],
                       **{k: v for k, v in obj.items() if k != "tile"})

        raise ValueError(f"Cannot parse WallAsset from keys: {list(obj.keys())}")


# register the classmethod as hook
converter.register_structure_hook(WallAsset, WallAsset._structure)


# @register_parse
@attrs.define
class Wall(Parseable):
    start: Position
    end: Position
    height: float = attrs.field(converter=float, default=2.0)
    width: float = attrs.field(converter=float,default =0.05)
    z_offset: float = attrs.field(converter=float, default=0.0)
    material: str = ''
    type_: str = "simple"
    assets: list[list["Wall"], list["Obstacle"],str] = attrs.field(init=False)

    def __attrs_post_init__(self):
        if self.type_ != "simple":
            self.assets = WallDescription.load(self.type_, self.start, self.end)

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
        if isinstance(value, dict):
            return converter.structure(value,cls)
        raise ValueError(f"Could not parse as wall: {value}")

@register_parse
@attrs.define
class WallDescription:
    @classmethod
    def load(
        cls,
        type_: str = "simple",
        start: Position | None = None,
        end: Position | None = None,
    ) -> list[list["Wall"], list["Obstacle"],str]:
        vec = np.array([end.x,end.y]) - np.array([start.x,start.y])
        angle = math.atan2(vec[1],vec[0]) + 3.14/2 
        # print("assets angle", angle)
        wall_assets_path = os.path.join(ass_dir,'entities','walls',str(type_) + '.yaml')
        with open(wall_assets_path) as f:
            data = yaml.safe_load(f)
            # print(data)
        fill, tile = [],[]
        fill_assets = [converter.structure(item, WallAsset) for item in data.get("main", []) if 'fill' in item]
        for fill_asset in fill_assets:
            fill.append(
                Wall(
                    start = Position(x = start.x + fill_asset.x_offset, y = start.y + fill_asset.y_offset),
                    end = Position(x = end.x - fill_asset.x_offset, y = end.y - fill_asset.y_offset),
                    height = fill_asset.height,
                    width = 0.075,
                    z_offset = fill_asset.z_offset,
                    material = fill_asset.material,
                )
            )
        tile_assets = [converter.structure(item, WallAsset) for item in data.get("main", []) if 'tile' in item]
        for tile_asset in tile_assets:
            if start.x == end.x: 
                num_assets = int((abs(start.y - end.y) - tile_asset.width - tile_asset.y_offset * 2) // tile_asset.every)
                if num_assets <=0:
                    pos_x = []
                    pos_y = []
                else:
                    pos_x = [start.x] * num_assets
                    if num_assets == 1:
                        pos_y = [(start.y + end.y)/2] 
                    else: 
                        if start.y > end.y:
                            pos_y = np.linspace(start.y - tile_asset.width/2 - tile_asset.y_offset , end.y + tile_asset.width/2 + tile_asset.y_offset, num = num_assets) 
                        else:
                            pos_y = np.linspace(start.y + tile_asset.width/2 + tile_asset.y_offset , end.y - tile_asset.width/2 - tile_asset.y_offset, num = num_assets) 
            elif start.y == end.y: 
                num_assets = int((abs(start.x - end.x) - tile_asset.width - tile_asset.x_offset * 2) // tile_asset.every)
                if num_assets <=0:
                    pos_x = []
                    pos_y = []
                else:
                    pos_y = [start.y] * num_assets
                    if num_assets == 1:
                        pos_x = [(start.x + end.x)/2]
                    else:
                        if start.x > end.x:
                            pos_x = np.linspace(start.x - tile_asset.width/2 - tile_asset.x_offset , end.x + tile_asset.width/2 + tile_asset.x_offset, num = num_assets) 
                        else:
                            pos_x = np.linspace(start.x + tile_asset.width/2 + tile_asset.x_offset , end.x - tile_asset.width/2 - tile_asset.x_offset, num = num_assets) 
            for i in range(len(pos_x)):
                tile.append(
                    Obstacle(
                        name = tile_asset.name+f"_{i}",
                        pose = Pose(
                            Position(x = pos_x[i], y = pos_y[i] + 0.02, z = tile_asset.z_offset ),
                            Orientation.from_yaw(angle)
                        ),
                        model = ObstacleLoader.bind(tile_asset.name),
                        type_ = "Wall",
                        extra = {},
                    )
                )
        return fill,tile,data.get('material',{}).get('material','')

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
            return converter.structure(value,cls)
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
    type_: str = attrs.field(converter=str)


@attrs.define
class DynamicObstacle(Obstacle):
    model: ModelWrapper = attrs.field(converter=model_parse(DynamicObstacleLoader, overrides=(ObstacleLoader,)))
    waypoints: list[Position]


@attrs.define
class Robot(Entity):
    model: ModelWrapper = attrs.field(converter=model_parse(RobotLoader))
