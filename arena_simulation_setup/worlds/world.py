import os

from arena_simulation_setup import ProviderBase, ass_dir

from .scenario import ScenarioProvider
from .map import Map


class WorldProvider(ProviderBase):

    @classmethod
    def list(cls) -> list[str]:
        return ['.generated'] + super().list()

    @property
    def scenario(self):
        return ScenarioProvider.bind(os.path.join(self.path, 'scenarios'))

    @property
    def map(self):
        return Map(os.path.join(self.path, 'map'))


World = WorldProvider.bind(os.path.join(ass_dir, 'worlds'))
