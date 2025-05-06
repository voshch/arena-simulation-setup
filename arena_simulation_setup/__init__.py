import os
import typing
import ament_index_python.packages

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

    @property
    def mappings(self) -> str:
        return os.path.join(
            self.dir,
            'mappings.yaml'
        )


class Obstacle(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'entities', 'obstacles', 'static')


class DynamicObstacle(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'entities', 'obstacles', 'dynamic')
