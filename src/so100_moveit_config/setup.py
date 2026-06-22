from setuptools import setup
from glob import glob
import os

setup(
    name='so100_moveit_config',
    version='0.1.0',
    packages=['so100_moveit_config'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/so100_moveit_config']),
        ('share/so100_moveit_config/config', glob('config/*')),
        ('share/so100_moveit_config/launch', glob('launch/*')),
    ],
)
