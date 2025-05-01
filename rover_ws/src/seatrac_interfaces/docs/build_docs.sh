#!/bin/bash
# Created by Nelson Durrant, Oct 2024
#
# Generates documentation for the ROS2 seatrac_interfaces package
# - The documentation can be accessed by opening the 'index.html'
#   file in the 'docs_output/seatrac_interfaces' directory

source ~/ros2_ws/install/setup.bash
rosdoc2 build --package-path ~/ros2_ws/src/seatrac_interfaces