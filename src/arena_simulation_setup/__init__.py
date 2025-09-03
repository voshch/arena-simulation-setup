import os
import typing

ass_dir: str
ab_dir: str

try:
    import ament_index_python.packages
    ass_dir = ament_index_python.packages.get_package_share_directory('arena_simulation_setup')
    ab_dir = ament_index_python.packages.get_package_share_directory('arena_bringup')
except ImportError:
    ass_dir = os.environ.get('ass_dir', '')
    ab_dir = os.environ.get('ab_dir', '')

T = typing.TypeVar('T', bound='ProviderBase')


class ProviderBase:

    # Class Methods: Provider
    _base_dir: typing.ClassVar[str]

    @classmethod
    def bind(cls: typing.Type[T], path: str) -> typing.Type[T]:
        return typing.cast(
            typing.Type[T],
            type('Bound' + cls.__name__, (cls,), dict(_base_dir=path))
        )

    @classmethod
    def _listdir(cls, path: str) -> list[str]:
        return list(sorted(f for f in os.listdir(path) if not f.startswith('.')))

    @classmethod
    def list(cls) -> list[str]:
        return cls._listdir(cls._base_dir)

    @classmethod
    def base_dir(cls) -> str:
        return cls._base_dir

    # Instance Methods: Providee
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return os.path.join(self._base_dir, self._name)
