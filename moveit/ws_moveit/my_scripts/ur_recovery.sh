#!/bin/bash
ROBOT_IP="192.168.1.102"
while true; do
  echo "Stopping robot and killing old MoveIt..."
  echo "stop" | nc -w 2 $ROBOT_IP 29999
  pkill -f "move_group" || true
  sleep 2
  echo "Launching ROS 2 driver..."
  timeout 30 ros2 launch ur_robot_driver ur_control.launch.py \
    ur_type:=ur3e \
    robot_ip:=$ROBOT_IP \
    headless_mode:=true \
    reverse_ip:=192.168.1.10 \
    launch_rviz:=false
  echo "Driver dropped, restarting in 3 seconds..."
  sleep 3
done
