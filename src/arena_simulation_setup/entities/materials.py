from __future__ import annotations

import os
import typing

import attrs
import yaml

from arena_simulation_setup import ProviderBase, Sources, ass_sources
from arena_simulation_setup.utils.cattrs import Serializable, converter


@attrs.define
class Material:
    url: str
    name: str

    DEFAULT: typing.ClassVar[str] = "default"

    def asdict(self) -> dict:
        return attrs.asdict(self)


class MaterialProvider(ProviderBase, Serializable):
    # TODO figure materials format and switch to Sources

    _materials_dict: typing.ClassVar[dict[str, dict]]
    _path: typing.ClassVar[str]

    @classmethod
    def DEFAULT(cls) -> MaterialProvider:
        return cls(Material.DEFAULT)

    @classmethod
    def bind(_cls, path: Sources):
        cls = super().bind(path)
        resolved = cls.resolve()
        if not resolved:
            raise ValueError(f"Path '' not found in sources: {cls._sources}")
        with open(resolved) as f:
            return type(
                'Bound' + cls.__name__,
                (
                    # super().bind(path),
                    cls,
                ),
                dict(
                    _path=path,
                    _materials_dict=yaml.safe_load(f)
                )
            )

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._materials_dict.keys())

    def load(self) -> Material:
        material = self._materials_dict.get(self._name)
        if material is None:
            raise FileNotFoundError(f'Material not found in {self._path}: {self._name}')
        return converter.structure(material, Material)

    def serialize(self) -> str:
        return self.name


WallMaterialLoader = MaterialProvider.bind(ass_sources('entities', 'materials', 'wall.yaml'))
FloorMaterialLoader = MaterialProvider.bind(ass_sources('entities', 'materials', 'floor.yaml'))
