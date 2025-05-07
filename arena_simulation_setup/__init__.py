import os
import typing

import ament_index_python.packages
import yaml

ass_dir = ament_index_python.packages.get_package_share_directory('arena_simulation_setup')


class _AssInterface:
    _base_dir: typing.ClassVar[str] = ass_dir
    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    @classmethod
    def base_dir(cls) -> str:
        return cls._base_dir

    @classmethod
    def list(cls) -> list[str]:
        return os.listdir(cls._base_dir)

    @property
    def dir(self) -> str:
        return os.path.join(
            self._base_dir,
            self._name,
        )


class World(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'worlds')

    @property
    def scenarios(self) -> list[str]:
        return os.listdir(
            os.path.join(
                self.dir,
                'scenarios'
            )
        )

    @property
    def obstacles(self) -> str:
        return os.path.join(
            self.dir,
            'map',
            'obstacles.yaml'
        )

    @property
    def walls(self) -> str:
        return os.path.join(
            self.dir,
            'map',
            'walls.yaml'
        )

    @property
    def zones(self) -> str:
        return os.path.join(
            self.dir,
            'map',
            'zones.yaml'
        )


class Robot(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'entities', 'robots')

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._cached_params = None

    @property
    def _model_params(self) -> dict[str, typing.Any]:
        if self._cached_params is None:
            with open(os.path.join(self.dir, 'model_params.yaml')) as f:
                self._cached_params = yaml.safe_load(f)
        return self._cached_params

    @property
    def mappings(self) -> str:
        return os.path.join(
            self.dir,
            'mappings.yaml'
        )

    @property
    def base_frame(self) -> str:
        return self._model_params.get('robot_base_frame', 'base_link')

    @property
    def odom_frame(self) -> str:
        return self._model_params.get('robot_odom_frame', 'odom')


class Obstacle(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'entities', 'obstacles', 'static')


class DynamicObstacle(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'entities', 'obstacles', 'dynamic')
