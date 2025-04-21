import os
import ament_index_python.packages


def get_model_directory(model: str) -> str:
    return os.path.join(
        ament_index_python.packages.get_package_share_directory('arena_simulation_setup'),
        'entities',
        'robots',
        model
    )
