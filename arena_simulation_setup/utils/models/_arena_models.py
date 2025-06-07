import typing
from arena_simulation_setup.utils.models import Model
from . import ITF_ModelLoader, ModelType


class _ArenaModelsLoaderBase(ITF_ModelLoader):

    prefix: typing.ClassVar[str] = 'arena_models://'
    model_type: typing.ClassVar[ModelType | None] = None

    @classmethod
    def load(cls, model_dir: str, model: str, loader_args: dict) -> Model | None:
        if cls.model_type is None:
            return None

        if model.startswith(cls.prefix):
            query = model[len(cls.prefix):]
            type_ = cls.model_type

            # TODO return arena_models result if successful
            return None

        return None


def BoundArenaModelsLoaderBase(type_: ModelType):
    class Derived(_ArenaModelsLoaderBase):
        model_type = type_
    return Derived
