import os

from . import _AssInterface


class Environment(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'configs', 'environment')


class Parametrized(_AssInterface):
    _base_dir = os.path.join(_AssInterface._base_dir, 'configs', 'parametrized')
