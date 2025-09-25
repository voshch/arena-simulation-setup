import os

from arena_simulation_setup import ProviderBase, ass_dir
from arena_simulation_setup.utils.models.model_loader import ModelLoader


class ObstacleModelProvider(ProviderBase):
    ...


ObstacleModel = ObstacleModelProvider.bind(os.path.join(ass_dir, 'entities', 'obstacles', 'static'))


loader = ModelLoader(ObstacleModel.base_dir())
