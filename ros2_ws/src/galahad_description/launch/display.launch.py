"""Bring up the Galahad model in RViz (no hardware required).

    ros2 launch galahad_description display.launch.py
    ros2 launch galahad_description display.launch.py gui:=false
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("galahad_description")
    urdf = os.path.join(pkg, "urdf", "galahad.urdf")
    rviz = os.path.join(pkg, "rviz", "galahad.rviz")
    robot_description = {"robot_description": open(urdf, encoding="utf-8").read()}

    gui = LaunchConfiguration("gui")
    use_rviz = LaunchConfiguration("rviz")

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true",
                              description="Start joint_state_publisher_gui"),
        DeclareLaunchArgument("rviz", default_value="true"),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[robot_description],
        ),
        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
            condition=IfCondition(gui),
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            condition=UnlessCondition(gui),
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", rviz],
            condition=IfCondition(use_rviz),
            output="screen",
        ),
    ])
