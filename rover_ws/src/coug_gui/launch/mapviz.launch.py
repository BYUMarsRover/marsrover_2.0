# Created by Nelson Durrant, Feb 2025
import launch
import os
import launch_ros
from ament_index_python.packages import get_package_share_directory

gui_dir = get_package_share_directory("coug_gui")
mapviz_config_file = os.path.join(gui_dir, "config", "mapviz_params.mvc")


def generate_launch_description():
    return launch.LaunchDescription(
        [
            launch_ros.actions.Node(
                package="mapviz",
                executable="mapviz",
                name="mapviz",
                parameters=[
                    {"config": mapviz_config_file},
                ],
            ),
            launch_ros.actions.Node(
                package="swri_transform_util",
                executable="initialize_origin.py",
                name="initialize_origin",
                remappings=[
                    ("fix", "mapviz/origin"), # set by the sync_origin node
                ],
            ),
            launch_ros.actions.Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="swri_transform",
                arguments=["0", "0", "0", "0", "0", "0", "map", "origin"],
            ),
        ]
    )
