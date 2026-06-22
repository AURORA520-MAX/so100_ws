import os
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("so_arm100", package_name="so100_moveit_config")
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
        )
        .planning_pipelines(
            pipelines=["ompl"],
            default_planning_pipeline="ompl",
        )
        .to_moveit_configs()
    )

    # 合并 moveit 参数和控制器参数
    params_dict = moveit_config.to_dict()
    params_dict["moveit_simple_controller_manager"] = {
        "controller_names": ["arm_controller"],
        "arm_controller": {
            "type": "FollowJointTrajectory",
            "joints": [
                "shoulder_pan", "shoulder_lift", "elbow_flex",
                "wrist_flex", "wrist_roll", "gripper",
            ],
            "action_ns": "follow_joint_trajectory",
        },
    }

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
            parameters=[moveit_config.robot_description],
        ),
        Node(
            package='moveit_ros_move_group',
            executable='move_group',
            name='move_group',
            output='screen',
            parameters=[params_dict],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.planning_pipelines,
                moveit_config.joint_limits,
            ],
        ),
    ])
