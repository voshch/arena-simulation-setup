import yaml

from arena_simulation_setup import ProviderBase, ass_sources_static


class EnvironmentProvider(ProviderBase):
    def load(self):
        with open(self.path, 'r') as f:
            return yaml.safe_load(f)


Environment = EnvironmentProvider.bind(ass_sources_static('configs', 'environment'))
