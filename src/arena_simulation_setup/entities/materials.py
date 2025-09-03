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
    material_name: str

    DEFAULT: typing.ClassVar[str] = "default"


class MaterialProvider(ProviderBase):
    _materials_dict: typing.ClassVar[dict[str, dict]]

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
        return converter.structure(self._materials_dict[self._name], Material)


WallMaterialLoader = MaterialProvider.bind(os.path.join(ass_dir, 'entities', 'materials', 'wall.yaml'))
FloorMaterialLoader = MaterialProvider.bind(os.path.join(ass_dir, 'entities', 'materials', 'floor.yaml'))
