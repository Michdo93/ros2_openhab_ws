"""Start the openHAB bridge with config/bridge.yaml or another parameter file.

ros2 launch openhab_bridge_cpp bridge.launch.py
ros2 launch openhab_bridge_cpp bridge.launch.py params:=/path/to/my_bridge.yaml
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default = os.path.join(
        get_package_share_directory("openhab_bridge_cpp"), "config", "bridge.yaml"
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params", default_value=default, description="parameter file of the bridge"
            ),
            Node(
                package="openhab_bridge_cpp",
                executable="openhab_bridge",
                name="openhab_bridge",
                parameters=[LaunchConfiguration("params")],
                output="screen",
                respawn=True,
                respawn_delay=5.0,
            ),
        ]
    )
