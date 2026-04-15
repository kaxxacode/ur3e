#!/bin/bash

xhost +local:docker
docker start moveit2_ur3_v2_container
docker exec -it moveit2_ur3_v2_container /bin/bash

# docker run -it --rm \
#   --network host \
#   --privileged \
#   -e DISPLAY=$DISPLAY \
#   -v /tmp/.X11-unix:/tmp/.X11-unix \
#   -v /dev/bus/usb:/dev/bus/usb \
#   -v ~/code/python-bootcamp/moveit/ur3_ws:/root/ur3_ws \
#   moveit_ur3