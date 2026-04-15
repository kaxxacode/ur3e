xhost +local:docker

# Remove old stopped container if it exists (won't affect running ones)
docker rm moveit2_ur3_v2_container 2>/dev/null || true

# 'up' reads the ports section and creates the bridge
docker compose up -d
docker exec -it moveit2_ur3_v2_container bash

# docker compose run --name moveit2_ur3_v2_container  moveit_dev

# docker run -it  \
#   --network host \
#   --privileged \
#   -e DISPLAY=$DISPLAY \
#   -v /tmp/.X11-unix:/tmp/.X11-unix \
#   -v /dev/bus/usb:/dev/bus/usb \
#   -v ~/code/python-bootcamp/moveit/ur3_ws/ws_moveit:/root/ws_moveit \
#   --name moveit2_ur3_v2_container  \
#   moveit2_ur3_v2
