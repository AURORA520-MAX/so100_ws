from setuptools import setup
from glob import glob
import os

package_name = "so100_description"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        (os.path.join("share", package_name, "urdf"), glob("urdf/*.urdf")),
        (os.path.join("share", package_name, "meshes"), glob("meshes/*.stl")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "minimal_jsp = so100_description.minimal_jsp:main",
        ],
    },
)
