# Created by Nelson Durrant, Mar 2025
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # https://github.com/ros/urdf_launch
    start_robot_state_publisher_cmd = IncludeLaunchDescription(
        PathJoinSubstitution(
            [FindPackageShare("urdf_launch"), "launch", "description.launch.py"]
        ),
        # Uncomment the below (and comment out the above) to see the robot model displayed in RViz
        # PathJoinSubstitution(
        #     [FindPackageShare("urdf_launch"), "launch", "display.launch.py"]
        # ),
        launch_arguments={
            "urdf_package": "coug_description",
            "urdf_package_path": PathJoinSubstitution(["urdf", "couguv.urdf.xacro"]),
        }.items(),
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # robot state publisher launch
    ld.add_action(start_robot_state_publisher_cmd)

    return ld
