#!/bin/bash
# Created by Braden Meyers & Nelson Durrant, Mar 2025
# 
# Sets up the rover environment with the ROS_DISCOVERY_SERVER environment variable
# https://docs.ros.org/en/humble/Tutorials/Advanced/Discovery-Server/Discovery-Server.html

function printError {
  	# print red
  	echo -e "\033[0m\033[31m[ERROR] $1\033[0m"
}

# Check if this script was run using 'source'
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    printError "Please source this script ('source disc_rover.sh')"
    exit 1
fi

export ROS_DISCOVERY_SERVER="localhost:11811"
