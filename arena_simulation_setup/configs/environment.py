import os

import yaml

from arena_simulation_setup import ProviderBase, ass_dir


class EnvironmentProvider(ProviderBase):
    def load(self):
        with open(self.path, 'r') as f:
            return yaml.safe_load(f)


Environment = EnvironmentProvider.bind(os.path.join(ass_dir, 'configs', 'environment'))
