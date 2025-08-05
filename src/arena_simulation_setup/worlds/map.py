import os


class Map:
    def __init__(self, path: str):
        self._path = path

    @property
    def path(self) -> str:
        return self._path

    @property
    def map_yaml(self) -> str:
        return os.path.join(self.path, 'map.yaml')

    @property
    def map_png(self) -> str:
        return os.path.join(self.path, 'map.png')
