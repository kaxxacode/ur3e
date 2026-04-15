# UR3e MoveIt2 Docker Setup


## Restart

1. Start Docker

1. Start XLaunch using saved config.

1. Connect camera to USB.

1. From Windows Powershell, map the camera to WSL2 Ubuntu:

    ```BASH
    usbipd list
    usbipd bind --busid 2-13
    usbipd attach --wsl --busid 2-13
    usbipd list
    ```

    Camera status should show "attached"

1. Start first container instance from bash:

    ```BASH
    cd ~/code/python-bootcamp/moveit/ur3_ws/ && ./start_ur3.sh

    # To open additional shells on same container
    docker exec -it moveit2_ur3_v2_container /bin/bash
    ```

1. Inside docker container, launch camera node:

    ```BASH
    ros2 launch realsense2_camera rs_launch.py \
        camera_name:=camera \
        align_depth.enable:=true \
        pointcloud.enable:=true \
        rgb_camera.profile:=640x480x15 \
        depth_module.profile:=640x480x15 \
        filters:=spatial,temporal
    ```

1. Launch VS Code, on the docker container. 

    On WSL2 Ubuntu, Open VS Code at the folder where `.devcontainer` is located. 
    VS Code will automatially prompt to reopen from the Container.

    ```BASH
    cd ~/code/python-bootcamp/moveit/ur3_ws && code .
    ```

1. Start additional docker container bash:

    ```BASH
    docker exec -it moveit2_ur3_v2_container /bin/bash
    ```

    ...build our setup

    ```BASH
    source /opt/ros/jazzy/setup.bash
    source ~/ws_moveit/install/setup.bash
    
    cd /root/ws_moveit
    
    colcon build --symlink-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release \
        --packages-select my_robot_moveit_config my_robot_description
    
    source ~/ws_moveit/install/setup.bash
    ```

    ...and launch MoveIt in RViz:

    ```BASH
    ros2 launch my_robot_moveit_config demo.launch.py
    ```

1. Configure RViz

    * Display | Global Options | Fixed Frame = 'world'
    * Add | rviz_default_plugins | RobotModel
    * Add | moveit_ros_visualization | MotionPlanning
    * Add | moveit_ros_visualization | PointCloud2

## Old Setup

1. Inside docker container, launch MoveIt 2 with UR3:

    ```BASH
    ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur3e \
        use_fake_hardware:=true \
        launch_rviz:=true \
        robot_ip:=192.168.0.11
    ```

    This may also works:

    ```BASH
    ros2 launch ur_description view_ur.launch.py ur_type:=ur3e
    ```

1. Inside docker container, bind camera with TCP:

    ```BASH
    ros2 run tf2_ros static_transform_publisher 0 0 0.05 0 0 0 wrist_3_link camera_link
    ```

1. From RViz add camera point cloud into the scene:

    * Click Add
    * Select 'By topic'
    * Browse to: /camera/camera/depth/color/points/PointCloud2
    * Click Ok


## Notes

- "Failed to connect to robot on IP 192.168.0.1" error is normal — ignore it
- Save all code to /root/ur3_ws inside the container
- This maps to ~/code/python-bootcamp/moveit/ur3_ws on your machine
- Files saved anywhere else in the container will be lost on exit
- Test cemara with: `realsense-viewer`

## One-Time Setup

1. Start Docker

1. Create docker image:

    ```BASH
     cd ~/code/python-bootcamp/moveit/ur3_ws/
     docker build  -t moveit2_ur3_v2  .
    ```

1. Start XLaunch using saved config.

1. Create docker container and start it:

    ```bash
    cd ~/code/python-bootcamp/moveit/ur3_ws/ && ./setup_ur3.sh
    ```

    Docker will now have a permanent container instance named `moveit2_ur3_v2_container`.


1. Install `lsusb` on the docker image, that allows you to troubleshoot camera issues:

    ```
    sudo apt update
    sudo apt install usbutils -y
    lsusb
    ```

## MoveIt Coding in Docker Container

We want to code within the Docker container using VS Code. However, VS Code is running on the host machine. The solution involves putting the `ws_moveit` folder on a shared volume and usig the `Dev Containers` VS Code extension.

This is complicated by the fact that `ws_moveit` is already included within the base MoveIt image. Thus, we need to copy the image `ws_moveit` folder to the host (WSL2 Ubuntu). We then mount it over the `ws_moveit` already present in the Docker container.

1. Copying `ws_moveit` from Docker image to Host

    ```BASH
    # Start a temporary container
    docker run -d --name temp_moveit moveit2_ur3_v2

    # Copy the folder from the container to your current host directory
    docker cp temp_moveit:/root/ws_moveit ./ws_moveit

    # Remove the temporary container
    docker rm -f temp_moveit
    ```

1. Update `setup_ur3.sh` to include a volume mapping for `ws_moveit`:

    ```
      -v ~/code/python-bootcamp/moveit/ur3_ws/ws_moveit:/root/ws_moveit
    ```

1. Create `.devcontainer/devcontainer.json` configuration file. This will tell the VS Code Dev Container extension, how to switch to the Docker Container rahter than running as if coding on the host.

1. Create docker container and start it:

    ```bash
     ~/code/python-bootcamp/moveit/ur3_ws/setup_ur3.sh
    ```

    Docker will now have a permanent container instance named `moveit2_ur3_v2_container`.

1. Open VS Code at the folder where `.devcontainer` is located. VS Code will automatially prompt to reopen from the Container.

    ```BASH
    cd ~/code/python-bootcamp/moveit/ur3_ws && code .
    ```

## Other

1. Running `detect_towers_ros.py`

    ```BASH
    # list of topics
    ros2 topic list

    # run tower detection script with GUI
    python3 ./my_scripts/detect_towers_ros.py --ros-args -p show_gui:=true

    # Run without gui
    python3 ./my_scripts/detect_towers_ros.py --ros-args -p show_gui:=false

    # Turn the GUI on instantly
    ros2 param set /tower_detector show_gui true

    # Turn it off again
    ros2 param set /tower_detector show_gui false

    # Kill "Yolo11 Detector" dialog
    pkill -9 python3

    ```

1. Networking Ur3e to MoveIt

    ```BASH

    # install networking tools on ubuntu
    apt-get update && apt-get install -y iproute2 iputils-ping netcat-openbsd telnet

    # Show ip address on Ubuntu
    ip addr show

    # or...
    hostname -I


    # Forward the UR Control Ports (30001-30004)
    netsh interface portproxy add v4tov4 listenport=30001 listenaddress=192.168.0.127 connectport=30001 connectaddress=172.30.4.188
    netsh interface portproxy add v4tov4 listenport=30002 listenaddress=192.168.0.127 connectport=30002 connectaddress=172.30.4.188
    netsh interface portproxy add v4tov4 listenport=50001 listenaddress=192.168.0.127 connectport=50001 connectaddress=172.30.4.188

    ros2 launch ur_bringup ur_control.launch.py \
    ur_type:=ur3e \
    robot_ip:=192.168.1.102 \
    reverse_ip:=192.168.1.100 \
    launch_rviz:=true

    nc -l -p 30002
    ```

1. Launching RVizz

    **Terminal 1:**
    ```bash
    while true; do
    ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur3e robot_ip:=192.168.1.102 headless_mode:=true reverse_ip:=192.168.1.10 launch_rviz:=false
    echo "Driver dropped, restarting in 5 seconds..."
    sleep 5
    done
    ```

    **Terminal 2:**
    ```bash
    ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur3e launch_rviz:=true
    ```

    Robot must be in **Remote Control** mode on the pendant. No program loaded or running.Memory updated. That's your confirmed working setup saved.
