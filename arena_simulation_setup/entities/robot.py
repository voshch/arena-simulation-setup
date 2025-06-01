import os
import typing

import yaml

from arena_simulation_setup import Interface, ass_dir
from arena_simulation_setup.utils.models.model_loader import ModelLoader


class Robot(Interface(os.path.join(ass_dir, 'entities', 'robots'))):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._cached_params = None

    @property
    def _model_params(self) -> dict[str, typing.Any]:
        if self._cached_params is None:
            with open(os.path.join(self.path, 'model_params.yaml')) as f:
                self._cached_params = yaml.safe_load(f)
        return self._cached_params

    @property
    def mappings(self) -> str:
        return os.path.join(
            self.path,
            'mappings.yaml'
        )

    @property
    def base_frame(self) -> str:
        return self._model_params.get('robot_base_frame', 'base_link')

    @property
    def odom_frame(self) -> str:
        return self._model_params.get('robot_odom_frame', 'odom')

    @property
    def control(self) -> dict:
        with open(os.path.join(self.path, 'control.yaml')) as f:
            return yaml.safe_load(f)


loader = ModelLoader(Robot.base_dir())
