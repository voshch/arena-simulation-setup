import collections

import attrs
import geometry_msgs.msg
import numpy as np


@attrs.frozen()
class Position:
    """
    2D position
    """
    x: float = attrs.field(converter=float)
    y: float = attrs.field(converter=float)


@attrs.frozen()
class PositionOrientation(Position):
    """
    2D position with 2D yaw
    """
    orientation: float = attrs.field(converter=float)

    @classmethod
    def from_pose(
        cls,
        pose: geometry_msgs.msg.Pose
    ) -> "PositionOrientation":
        """
        parse geometry_msgs.msg.Pose
        """
        return cls(
            x=pose.position.x,
            y=pose.position.y,
            orientation=euler_from_quaternion(
                x=pose.orientation.x,
                y=pose.orientation.y,
                z=pose.orientation.z,
                w=pose.orientation.w
            )[2]
        )

    def to_pose(self) -> geometry_msgs.msg.Pose:
        """
        return self as geometry_msgs.msg.Pose
        """

        quat = quaternion_from_euler(
            0.0,
            0.0,
            self.orientation,
            axes="xyzs"
        )

        pose = geometry_msgs.msg.Pose(
            position=geometry_msgs.msg.Point(
                x=self.x,
                y=self.y,
            ),
            orientation=geometry_msgs.msg.Quaternion(
                x=quat[0],
                y=quat[1],
                z=quat[2],
                w=quat[3],
            )
        )

        return pose


@attrs.frozen()
class PositionRadius(Position):
    """
    2D position with 2D yaw
    """
    radius: float = attrs.field(converter=lambda x: max(0., float(x)))


def quaternion_from_euler(roll: float, pitch: float, yaw: float,
                          **kwargs) -> tuple[float, float, float, float]:
    """
    https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Source_code
    """
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)

    axes: str = str(kwargs.get('axes', 'sxyz'))
    assert len(set(axes)) == len(axes), 'axes contains duplicate entries'
    assert len(set(axes).difference(set('sxyz'))
               ) == 0, 'axes contains invalid entries. allowed: s,x,y,z'

    quat = dict(
        s=cr * cp * cy + sr * sp * sy,
        x=sr * cp * cy - cr * sp * sy,
        y=cr * sp * cy + sr * cp * sy,
        z=cr * cp * sy - sr * sp * cy
    )

    return tuple(quat[axis] for axis in axes)


def euler_from_quaternion(
    x: float,
    y: float,
    z: float,
    w: float,
    **kwargs
) -> tuple[float, float, float]:
    """
        https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Source_code_2
    """

    q = collections.namedtuple('Quaternion', ('x', 'y', 'z', 'w'))(
        x=x,
        y=y,
        z=z,
        w=w,
    )
    # maybe change input parsing later

    sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    sinp = np.sqrt(1 + 2 * (q.w * q.y - q.x * q.z))
    cosp = np.sqrt(1 - 2 * (q.w * q.y - q.x * q.z))
    pitch = 2 * np.arctan2(sinp, cosp) - np.pi / 2

    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def angle_diff(a: float, b: float) -> float:
    """
    returns difference of angles
    """
    A = (a - b) % 2 * np.pi
    B = (b - a) % 2 * np.pi
    return -A if A < B else B
