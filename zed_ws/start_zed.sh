#!/bin/bash
# This script is helpful for quick starting up the wrapper when you have to restart it. 
export ROS_DISCOVERY_SERVER=localhost:11811
source ~/zed_ws/install/setup.bash
ros2 launch zed_wrapper zed_camera.launch.py camera_model:=zed2
