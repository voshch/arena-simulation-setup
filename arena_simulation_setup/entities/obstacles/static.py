import os

from arena_simulation_setup import ProviderBase, ass_dir
from arena_simulation_setup.utils.models.model_loader import ModelLoader


class ObstacleProvider(ProviderBase):
    ...


Obstacle = ObstacleProvider.bind(os.path.join(ass_dir, 'entities', 'obstacles', 'static'))


loader = ModelLoader(Obstacle.base_dir())
