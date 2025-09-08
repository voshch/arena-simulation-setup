from __future__ import annotations

import enum
import itertools
import os
import typing
from collections.abc import Iterator, Sequence

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
    _sources: typing.ClassVar[Sources]

    @classmethod
    def bind(cls: typing.Type[T], path: SourcesProtocol) -> typing.Type[T]:
        return typing.cast(
            typing.Type[T],
            type('Bound' + cls.__name__, (cls,), dict(_sources=path))
        )

    @classmethod
    def _listdir(cls, path: str) -> Sequence[str]:
        if not os.path.exists(path):
            return ()
        return tuple(sorted(f for f in os.listdir(path) if not f.startswith('.')))

    @classmethod
    def list(cls) -> Sequence[str]:
        return tuple(sorted(set(itertools.chain(*map(cls._listdir, cls._sources)))))

    @classmethod
    def base_dir(cls) -> str:
        return cls._sources

    @classmethod
    def resolve(cls, *suffix: str) -> str | None:
        resolved = next(filter(os.path.exists, map(lambda x: os.path.join(x, *suffix), cls._sources)), None)
        return resolved

    # Instance Methods: Provider
    def __new__(cls, obj: object):
        # don't rebind
        if issubclass(type(obj), cls):
            return obj
        return super().__new__(cls)

    def __init__(self, name: str) -> None:
        if hasattr(self, '_name'):
            return
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        resolved = self.resolve(self.name)
        if resolved is None:
            raise FileNotFoundError(f"Could not find {self.name} in {self._sources}")
        return resolved


class SourcesProtocol(typing.Protocol):
    def __iter__(self) -> Iterator[str]:
        ...

    def __call__(self, *suffix: str) -> SourcesProtocol:
        ...


class SourcesContainer(dict):
    class Key(enum.Enum):
        GLOBAL = enum.auto()
        WORLD = enum.auto()

    def sources(self) -> Iterator[str]:
        return filter(None, (self.get(self.Key.WORLD), self.get(self.Key.GLOBAL)))


class StaticSources(SourcesProtocol):
    """
    Static source directories
    """

    def __init__(self, *s: str) -> None:
        self._s: tuple[str, ...] = s

    def __iter__(self) -> Iterator[str]:
        yield from self._s

    def __repr__(self) -> str:
        return f"StaticSources({list(self)})"

    def __call__(self, *suffix: str) -> StaticSources:
        return StaticSources(*(os.path.join(s, *suffix) for s in self._s))


class Sources(SourcesProtocol):
    """
    Dynamic source directories
    """

    def __iter__(self) -> Iterator[str]:
        for x in self.__sources.sources():
            yield os.path.join(x, self.__suffix)

    def __repr__(self) -> str:
        return f"Sources({list(self)})"

    def __hash__(self) -> int:
        return hash((self.__suffix, *self.__sources.sources()))

    def __init__(self, sources: SourcesContainer, suffix: str = '') -> None:
        self.__sources: SourcesContainer = sources
        self.__suffix: str = suffix

    def __call__(self, *suffix: str) -> Sources:
        return Sources(self.__sources, os.path.join(self.__suffix, *suffix))


_ass_sources = SourcesContainer({SourcesContainer.Key.GLOBAL: ass_dir})


def set_world_dir(world_dir: str | None) -> None:
    """
    Set the world directory dynamic source resolution.
    """
    _ass_sources[SourcesContainer.Key.WORLD] = world_dir


ass_sources = Sources(_ass_sources)
ass_sources_static = StaticSources(ass_dir)
