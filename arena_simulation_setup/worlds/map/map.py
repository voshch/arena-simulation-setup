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
    def obstacles(self) -> str:
        return os.path.join(self.path, 'obstacles.yaml')

    @property
    def walls(self) -> str:
        return os.path.join(self.path, 'walls.yaml')

    @property
    def zones(self) -> str:
        return os.path.join(self.path, 'zones.yaml')
