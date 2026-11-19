"""Bridge plus state listener in one go.

    ros2 launch openhab_examples bridge_and_listener.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    bridge = os.path.join(
        get_package_share_directory("openhab_bridge"), "launch", "bridge.launch.py"
    )
    return LaunchDescription(
        [
            IncludeLaunchDescription(PythonLaunchDescriptionSource(bridge)),
            Node(package="openhab_examples", executable="state_listener", output="screen"),
        ]
    )
