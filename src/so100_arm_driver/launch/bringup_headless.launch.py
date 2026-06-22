"""Headless bringup: driver + robot_state_publisher (no GUI)"""
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    urdf_path = os.path.join(
        get_package_share_directory("so100_description"),
        "urdf", "so100.urdf"
    )
    with open(urdf_path, "r") as f:
        robot_desc = f.read()

    return LaunchDescription([
        Node(
            package="so100_arm_driver",
            executable="servo_driver",
            name="so100_arm_driver",
            parameters=[{"port": "/dev/ttyUSB0", "baudrate": 9600}],
            output="screen",
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            parameters=[{"robot_description": robot_desc}],
            output="screen",
        ),
    ])
