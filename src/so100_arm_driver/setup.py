from setuptools import setup
from glob import glob
import os

package_name = "so100_arm_driver"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "servo_driver = so100_arm_driver.servo_driver:main",
            "calibrate_joint = so100_arm_driver.calibrate_joint:main",
            "repeat_motion = so100_arm_driver.repeat_motion:main",
        ],
    },
)
