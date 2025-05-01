# Create by Nelson Durrant, Feb 2025
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
import launch_ros.actions
import os
import launch.actions


def generate_launch_description():
    
    loc_dir = get_package_share_directory("coug_localization")
    rl_params_file = os.path.join(loc_dir, "config", "localization_params.yaml")

    return LaunchDescription(
        [
            launch.actions.DeclareLaunchArgument(
                "output_final_position", default_value="false"
            ),
            launch.actions.DeclareLaunchArgument(
                "output_location", default_value="~/dual_ekf_navsat_example_debug.txt"
            ),
            # https://docs.ros.org/en/melodic/api/robot_localization/html/state_estimation_nodes.html
            launch_ros.actions.Node(
                package="robot_localization",
                executable="ekf_node",
                name="ekf_filter_node_odom",
                output="screen",
                parameters=[rl_params_file],
                remappings=[("odometry/filtered", "odometry/local")],
            ),
            # https://docs.ros.org/en/melodic/api/robot_localization/html/state_estimation_nodes.html
            launch_ros.actions.Node(
                package="robot_localization",
                executable="ekf_node",
                name="ekf_filter_node_map",
                output="screen",
                parameters=[rl_params_file],
                remappings=[("odometry/filtered", "odometry/global")],
            ),
            # https://docs.ros.org/en/melodic/api/robot_localization/html/navsat_transform_node.html
            launch_ros.actions.Node(
                package="robot_localization",
                executable="navsat_transform_node",
                name="navsat_transform",
                output="screen",
                parameters=[rl_params_file],
                remappings=[
                    ("imu/data", "coug1/modem_imu"),
                    ("gps/fix", "gps/fix"),
                    ("gps/filtered", "gps/filtered"),
                    ("odometry/gps", "odometry/gps"),
                    ("odometry/filtered", "odometry/global"),
                ],
            ),
            launch_ros.actions.Node(
                package="coug_localization",
                executable="sync_origin",
                output="screen",
                parameters=[rl_params_file],
            ),
            launch_ros.actions.Node(
                package="coug_localization",
                executable="gps_fix",
                output="screen",
                parameters=[rl_params_file],
            ),
            launch_ros.actions.Node(
                package="coug_localization",
                executable="dvl_odom",
                output="screen",
                parameters=[rl_params_file],
            ),
        ]
    )
