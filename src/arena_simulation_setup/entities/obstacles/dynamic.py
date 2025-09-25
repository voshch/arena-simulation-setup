import os

from arena_simulation_setup import ProviderBase, ass_dir
from arena_simulation_setup.utils.models.model_loader import ModelLoader


class DynamicObstacleModelProvider(ProviderBase):
    ...


DynamicObstacleModel = DynamicObstacleModelProvider.bind(os.path.join(ass_dir, 'entities', 'obstacles', 'dynamic'))

loader = ModelLoader(DynamicObstacleModel.base_dir())
