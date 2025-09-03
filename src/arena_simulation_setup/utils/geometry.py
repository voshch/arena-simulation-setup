from __future__ import annotations

import collections
import collections.abc
import math
import typing

import attrs
import numpy as np

from arena_simulation_setup.utils.cattrs import Idempotent

try:
    import geometry_msgs.msg  # type: ignore # noqa: F401
except ImportError:
    class _uninstanceable(object):
        """
        class that cannot be instantiated
        """

        def __new__(cls, *args, **kwargs):
            raise TypeError(f"installation of geometry_msgs is required to use {cls.__name__}")

        def __init__(self, *args, **kwargs):
            raise TypeError(f"installation of geometry_msgs is required to use {self.__class__.__name__}")

        def __getattribute__(self, name: str):
            raise TypeError(f"installation of geometry_msgs is required to use {self.__class__.__name__}.{name}")

    class geometry_msgs:
        """
        polyfill geometry_msgs.msg
        """

        class msg:
            class Point(_uninstanceable):
                ...

            class Quaternion(_uninstanceable):
                ...

            class Pose(_uninstanceable):
                ...

from arena_simulation_setup.utils.cattrs import Parseable, attrs_sequence, register_parse

EulerOrder = typing.Literal['xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx']
_EulerIndices: dict[str, tuple[int, int, int]] = {
    'xyz': (0, 1, 2),
    'xzy': (0, 2, 1),
    'yxz': (1, 0, 2),
    'yzx': (1, 2, 0),
    'zxy': (2, 0, 1),
    'zyx': (2, 1, 0),
}


@attrs.define
class Vector:
    x: float = attrs.field(converter=float)
    y: float = attrs.field(converter=float)
    z: float = attrs.field(converter=float, default=0.0)

    def __add__(self, other: Position) -> Position:
        return Position(
            x=self.x + other.x,
            y=self.y + other.y,
            z=self.z + other.z
        )

    def __sub__(self, other: Position) -> Position:
        return Position(
            x=self.x - other.x,
            y=self.y - other.y,
            z=self.z - other.z
        )

    def __mul__(self, other: float) -> Position:
        return Position(
            x=self.x * other,
            y=self.y * other,
            z=self.z * other
        )

    def __rmul__(self, other: float) -> Position:
        return self * other

    def __truediv__(self, other: float) -> Position:
        return Position(
            x=self.x / other,
            y=self.y / other,
            z=self.z / other
        )

    def norm(self, n: float = 2) -> float:
        """
        return norm of position vector
        """
        return (self.x ** n + self.y ** n + self.z ** n) ** (1 / n)

    def normalized(self) -> Position:
        return self / (self.norm() or 1)

    def to_orientation(self) -> Orientation:
        """
        return orientation of vector
        """
        yaw = math.atan2(self.y, self.x)
        pitch = math.atan2(-self.z, math.sqrt(self.x * self.x + self.y * self.y))
        return Orientation.from_euler((0, pitch, yaw), order='zyx')


@register_parse
@attrs_sequence(float)
@attrs.define
class Position(Parseable, Idempotent, Vector):
    """
    3D position
    """

    @classmethod
    def parse(cls, value: geometry_msgs.msg.Point | collections.abc.Sequence[float]) -> Position:
        """
        parse value into Position
        formats: [x,y], [x,y,z]
        """
        if isinstance(value, geometry_msgs.msg.Point):
            return cls.from_msg(value)

        if len(value) == 3:
            return cls(*value)

        if len(value) == 2:
            return cls(value[0], value[1], 0.0)

        raise ValueError(
            f"Translation must be [x,y] or [x,y,z], got {value}"
        )

    @classmethod
    def from_msg(
        cls,
        point: geometry_msgs.msg.Point
    ) -> "Position":
        """
        parse geometry_msgs.msg.Point
        """
        return cls(
            x=point.x,
            y=point.y,
            z=point.z
        )

    def to_msg(self) -> geometry_msgs.msg.Point:
        """
        return self as geometry_msgs.msg.Point
        """
        return geometry_msgs.msg.Point(
            x=self.x,
            y=self.y,
            z=self.z
        )


@register_parse
@attrs_sequence(float)
@attrs.define
class Orientation(Parseable, Idempotent):
    """
    3D orientation
    """

    w: float = attrs.field(converter=float)
    x: float = attrs.field(converter=float)
    y: float = attrs.field(converter=float)
    z: float = attrs.field(converter=float)

    @classmethod
    def parse(cls, value: geometry_msgs.msg.Quaternion | collections.abc.Sequence[float] | float) -> Orientation:
        """
        parse value into Orientation
        formats: yaw, [roll, pitch, yaw], [w,x,y,z]
        """
        if isinstance(value, geometry_msgs.msg.Quaternion):
            return cls.from_msg(typing.cast(geometry_msgs.msg.Quaternion, value))

        if isinstance(value, collections.abc.Sequence):
            if len(value) == 4:
                return cls(*value)

            if len(value) == 3:
                return cls.from_euler((value[0], value[1], value[2]))

        if isinstance(value, float):
            return cls.from_euler((0, 0, value), order='xyz')

        raise ValueError(f"could not parse Orientation from {value}")

    @classmethod
    def identity(cls) -> Orientation:
        return cls(1.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_msg(
        cls,
        quaternion: geometry_msgs.msg.Quaternion
    ) -> "Orientation":
        """
        parse geometry_msgs.msg.Quaternion
        """
        return cls(
            w=quaternion.w,
            x=quaternion.x,
            y=quaternion.y,
            z=quaternion.z
        )

    def to_msg(self) -> geometry_msgs.msg.Quaternion:
        """
        return self as geometry_msgs.msg.Quaternion
        """
        return geometry_msgs.msg.Quaternion(
            w=self.w,
            x=self.x,
            y=self.y,
            z=self.z
        )

    @classmethod
    def from_euler(cls, angles: typing.Tuple[float, float, float], order: EulerOrder = 'xyz') -> Orientation:
        x, y, z = (angles[index] for index in _EulerIndices[order])

        cr = math.cos(x * 0.5)
        sr = math.sin(x * 0.5)
        cp = math.cos(y * 0.5)
        sp = math.sin(y * 0.5)
        cy = math.cos(z * 0.5)
        sy = math.sin(z * 0.5)

        return cls(
            w=cr * cp * cy + sr * sp * sy,
            x=sr * cp * cy - cr * sp * sy,
            y=cr * sp * cy + sr * cp * sy,
            z=cr * cp * sy - sr * sp * cy,
        )

    def to_euler(self, order: EulerOrder = 'xyz') -> tuple[float, float, float]:
        """
        return euler angles
        """
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        result: list[float] = [0, 0, 0]
        for (index, value) in zip(_EulerIndices[order], (roll, pitch, yaw)):
            result[index] = value

        return (result[0], result[1], result[2])

    @classmethod
    def from_yaw(cls, yaw: float) -> Orientation:
        """
        return Orientation from yaw angle
        """
        return cls.from_euler((0, 0, yaw), 'xyz')

    def to_yaw(self) -> float:
        """
        return yaw angle
        """
        return self.to_euler()[2]

    def __mul__(self, other: Orientation) -> Orientation:
        return Orientation(
            w=self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            x=self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            y=self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            z=self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
        )


@register_parse
@attrs.define
class Pose(Parseable, Idempotent):
    """
    3D pose
    """

    position: Position = attrs.field(factory=lambda: Position(0, 0))
    orientation: Orientation = attrs.field(factory=lambda: Orientation(1, 0, 0, 0))

    @classmethod
    def parse(cls, value: geometry_msgs.msg.Pose | collections.abc.Sequence[float] | collections.abc.Sequence[collections.abc.Sequence[float]]) -> Pose:
        """
        parse value into Pose
        formats: [x,y], [x,y,yaw], [x,y,z,roll,pitch,yaw], [x,y,z,w,x,y,z], [[*position], [*orientation]]
        """
        if isinstance(value, geometry_msgs.msg.Pose):
            return cls.from_msg(value)

        # direct sequence
        if all(isinstance(v, (int, float)) for v in value):
            value = typing.cast(typing.Sequence[float], value)

            if len(value) == 2:
                return cls(
                    Position(x=value[0], y=value[1], z=0.0),
                    Orientation(w=1.0, x=0.0, y=0.0, z=0.0)
                )

            if len(value) == 3:
                return cls(
                    Position(x=value[0], y=value[1], z=0.0),
                    Orientation.from_yaw(value[2])
                )

            if len(value) in (6, 7):
                return cls(
                    position=Position.parse(value[:3]),
                    orientation=Orientation.parse(value[3:])
                )

        # split sequence
        if len(value) == 2 and all(isinstance(v, collections.abc.Sequence) for v in value) and all(isinstance(n, (int, float)) for v in value for n in v):
            value = typing.cast(typing.Sequence[typing.Sequence[float]], value)
            return cls(
                position=Position.parse(value[0]),
                orientation=Orientation.parse(value[1])
            )

        raise ValueError(f"could not parse Pose from {value}")

    @classmethod
    def from_msg(
        cls,
        pose: geometry_msgs.msg.Pose
    ) -> "Pose":
        """
        parse geometry_msgs.msg.Pose
        """
        return cls(
            position=Position.from_msg(pose.position),
            orientation=Orientation.from_msg(pose.orientation)
        )

    def to_msg(self) -> geometry_msgs.msg.Pose:
        """
        return self as geometry_msgs.msg.Pose
        """
        return geometry_msgs.msg.Pose(
            position=self.position.to_msg(),
            orientation=self.orientation.to_msg()
        )

    def to_2d(self) -> tuple[float, float, float]:
        """
        return self as (x, y, yaw)
        """
        return (self.position.x, self.position.y, self.orientation.to_yaw())


@register_parse
@attrs_sequence(float)
@attrs.define
class PositionRadius(Position, Idempotent):
    radius: float = attrs.field(converter=float, default=1.0)

    @classmethod
    def parse(cls, value: collections.abc.Sequence[float]) -> PositionRadius:
        """
        parse value into PositionRadius
        formats: [x,y,radius], [x,y,z,radius]
        """
        if len(value) == 3:
            return cls(*value)

        if len(value) == 2:
            return cls(value[0], value[1], 1.0)

        raise ValueError(f"PositionRadius must be [x,y] or [x,y,z,radius], got {value}")


def angle_diff(a: float, b: float) -> float:
    """
    returns difference of angles
    """
    A = (a - b) % 2 * np.pi
    B = (b - a) % 2 * np.pi
    return -A if A < B else B
