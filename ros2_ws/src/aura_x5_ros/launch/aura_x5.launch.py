"""Unified ROS 2 launch file for AURA-X5 on D-Robotics RDK X5."""
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description() -> LaunchDescription:
    pkg_share = get_package_share_directory("aura_x5_ros")
    params_file = os.path.join(pkg_share, "config", "aura_x5_params.yaml")

    return LaunchDescription([
        Node(
            package="aura_x5_ros",
            executable="sensor_node",
            name="aura_sensor_node",
            output="screen",
            parameters=[params_file],
        ),
        Node(
            package="aura_x5_ros",
            executable="bpu_perception_node",
            name="aura_bpu_perception_node",
            output="screen",
            parameters=[params_file],
        ),
        Node(
            package="aura_x5_ros",
            executable="safety_gate_node",
            name="aura_safety_gate_node",
            output="screen",
            parameters=[params_file],
        ),
        Node(
            package="aura_x5_ros",
            executable="actuator_ui_bridge_node",
            name="aura_actuator_ui_bridge_node",
            output="screen",
            parameters=[params_file],
        ),
    ])
