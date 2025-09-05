from __future__ import annotations

import os
import typing

import attrs
import yaml

from arena_simulation_setup import ProviderBase, ass_dir
from arena_simulation_setup.utils.cattrs import converter


@attrs.define
class Material:
    url: str
    name: str

    DEFAULT: typing.ClassVar[str] = "default"

    def asdict(self) -> dict:
        return attrs.asdict(self)


class MaterialProvider(ProviderBase):
    _materials_dict: typing.ClassVar[dict[str, dict]]

    @classmethod
    def DEFAULT(cls) -> MaterialProvider:
        return cls(Material.DEFAULT)

    @classmethod
    def bind(cls, path: str) -> MaterialProvider:
        c = super().bind(path)
        with open(path) as f:
            c._materials_dict = yaml.safe_load(f)
        return c

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._materials_dict.keys())

    def load(self) -> Material:
        material = self._materials_dict.get(self._name)
        if material is None:
            raise FileNotFoundError(f'Material not found in {self._path}: {self._name}')
        return converter.structure(material, Material)


WallMaterialLoader = MaterialProvider.bind(os.path.join(ass_dir, 'entities', 'materials', 'wall.yaml'))
FloorMaterialLoader = MaterialProvider.bind(os.path.join(ass_dir, 'entities', 'materials', 'floor.yaml'))
