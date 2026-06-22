import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    desc_pkg = get_package_share_directory('so100_description')
    config_pkg = get_package_share_directory('so100_moveit_config')

    urdf_path = os.path.join(desc_pkg, 'urdf', 'so100.urdf')
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    srdf_path = os.path.join(config_pkg, 'config', 'so100.srdf')
    with open(srdf_path, 'r') as f:
        srdf_content = f.read()

    kin_path = os.path.join(config_pkg, 'config', 'kinematics.yaml')
    with open(kin_path, 'r') as f:
        kin_content = f.read()

    limits_path = os.path.join(config_pkg, 'config', 'joint_limits.yaml')
    with open(limits_path, 'r') as f:
        limits_content = f.read()

    return LaunchDescription([
        Node(
            package='so100_arm_driver',
            executable='servo_driver',
            name='so100_arm_driver',
            parameters=[{'port': '/dev/ttyUSB0', 'baudrate': 9600}],
            output='screen',
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}],
        ),
        Node(
            package='moveit_ros_move_group',
            executable='move_group',
            name='move_group',
            output='screen',
            parameters=[
                {'robot_description': robot_desc},
                {'robot_description_semantic': srdf_content},
                {'robot_description_kinematics': kin_content},
                {'robot_description_planning': {'joint_limits': limits_content}},
                {'planning_plugin': 'ompl_interface/OMPLPlanner'},
            ],
        ),
    ])
