from glob import glob
import os

from setuptools import setup

package_name = 'simulation-setup'

setup(
    name=package_name,
    version='1.0.0',
    packages=[],  # No Python modules
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Will recursively track all .yaml files in the entities/robots directory and its subdirectories.
        *[
            (os.path.join('share', package_name, os.path.dirname(f)), [f])
            for f in glob('entities/robots/**/*.yaml', recursive=True)
        ]
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='NamTruongTran',
    maintainer_email='trannamtruong98@gmail.com',
    description='simulation-setup.',
    license='BSD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)