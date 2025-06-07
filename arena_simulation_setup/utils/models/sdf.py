import os

from . import Model, ITF_ModelLoader, ModelType, _ModelLoader
from ._arena_models import BoundArenaModelsLoaderBase


@_ModelLoader.model(ModelType.SDF)
class ArenaModelsLoader_SDF(BoundArenaModelsLoaderBase(ModelType.SDF)):
    ...


@_ModelLoader.model(ModelType.SDF)
class ModelLoader_SDF(ITF_ModelLoader):

    @classmethod
    def load(cls, model_dir, model, loader_args):
        model_path = os.path.join(model_dir, model, "sdf", f"{model}.sdf")
        try:
            with open(model_path) as f:
                return Model(
                    type=ModelType.SDF,
                    name=model,
                    description=f.read(),
                    path=model_path
                )
        except FileNotFoundError:
            pass
        return None
