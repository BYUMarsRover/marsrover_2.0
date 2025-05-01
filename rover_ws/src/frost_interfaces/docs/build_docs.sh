#!/bin/bash
# Created by Nelson Durrant, Oct 2024
#
# Generates documentation for the ROS2 frost_interfaces package
# - The documentation can be accessed by opening the 'index.html'
#   file in the 'docs_output/frost_interfaces' directory

source ~/ros2_ws/install/setup.bash
rosdoc2 build --package-path ~/ros2_ws/src/frost_interfaces