#!/bin/bash

xhost +local:docker
docker start moveit2_ur3_container
docker exec -it moveit2_ur3_container /bin/bash

# docker run -it --rm \
#   --network host \
#   --privileged \
#   -e DISPLAY=$DISPLAY \
#   -v /tmp/.X11-unix:/tmp/.X11-unix \
#   -v /dev/bus/usb:/dev/bus/usb \
#   -v ~/code/ur3e/moveit:/root/ur3_ws \
#   moveit_ur3