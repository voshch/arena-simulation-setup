from __future__ import annotations

import os
import typing

import attrs
import yaml

from arena_simulation_setup import ProviderBase, Sources, ass_sources
from arena_simulation_setup.utils.cattrs import Serializable, converter


@attrs.define
class Material:
    url: str  # TODO rename to path
    name: str

    DEFAULT: typing.ClassVar[str] = "default"

    def asdict(self) -> dict:
        return attrs.asdict(self)


class MaterialProvider(ProviderBase, Serializable):
    _path: typing.ClassVar[str]

    @classmethod
    def DEFAULT(cls) -> MaterialProvider:
        return cls(Material.DEFAULT)

    def load(self) -> Material:
        resolved = self.resolve(self.name, fn=os.path.isdir)
        if resolved is None:
            raise FileNotFoundError(f'Material {self.name} not found')
        return Material(
            name=self.name,
            url=os.path.join(resolved, f'{self.name}.mdl'),
        )

    def serialize(self) -> str:
        return self.name


MaterialLoader = MaterialProvider.bind(ass_sources('entities', 'materials'))
