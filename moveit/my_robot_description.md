## UR3 Project Setup

## Creating my_robot_description Package

1. Inside the moveit container create pkg

    ```BASH
    cd /root/ws_moveit/src
    ros2 pkg create --build-type ament_cmake my_robot_description
    ```

1. Move CAD STL files into project:

    ```BASH
    cd /root/ws_moveit/src
    mkdir meshes urdf
    ```

    Copy STL files to `meshes` folder

1. Open package from VC Code. Run this from WSL2 Ubuntu, and allow reopenning within container:

    ```BASH
    cd ~/code/python-bootcamp/moveit/ur3_ws && code .
    ```

1. Edit `my_robot_description/CMakeLists.txt` 

    ```
    # ... other stuff
    install(DIRECTORY
    meshes
    urdf
    DESTINATION share/${PROJECT_NAME}
    )

    ament_package()
    ```

1. Create `my_robot_description/urdf/ur3e_setup.urdf.xacro` file, describing the setup.

1. Build package:

    ```BASH
    source /opt/ros/jazzy/setup.bash
    source ~/ws_moveit/install/setup.bash
    
    cd /root/ws_moveit
    
    colcon build --symlink-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release \
        --packages-select my_robot_moveit_config my_robot_description
    
    source install/setup.bash
    ```

1. Verify:

    ```BASH
    xacro /root/ws_moveit/src/my_robot_description/urdf/ur3e_setup.urdf.xacro > test.urdf
    check_urdf  test.urdf
    ```

1. Start Rviz with robot setup:

    ```BASH
    ros2 launch ur_description view_ur.launch.py \
        ur_type:=ur3e \
        description_file:=/root/ws_moveit/src/my_robot_description/urdf/ur3e_setup.urdf.xacro
    ```

## Adding Configuration Package

1. Create a configuration package:

    ```BASH
    cd /root/ws_moveit/src

    mkdir -p my_robot_moveit_config/config
    mkdir -p my_robot_moveit_config/launch
    touch my_robot_moveit_config/config/ur3e_with_vision.srdf
    touch my_robot_moveit_config/launch/demo.launch.py
    ```

1. Verify that we have no overlaps between parts. This will also add more collision rules.

    ```BASH
    ros2 run moveit_setup_assistant collisions_updater \
    --urdf /root/ws_moveit/src/my_robot_description/urdf/ur3e_setup.urdf.xacro \
    --srdf /root/ws_moveit/src/my_robot_moveit_config/config/ur3e_with_vision.srdf \
    --output /root/ws_moveit/src/my_robot_moveit_config/config/ur3e_with_vision.srdf
    ```

1. Configure the `my_robot_moveit_config` package and CMakeLists

    ```BASH
    touch /root/ws_moveit/src/my_robot_moveit_config/package.xml
    touch /root/ws_moveit/src/my_robot_moveit_config/CMakeLists.txt
    ```

1. Rebuild:

    ```BASH
    cd /root/ws_moveit

    colcon build --symlink-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release \
        --packages-select my_robot_moveit_config my_robot_description
    
    source install/setup.bash

    ros2 launch my_robot_moveit_config demo.launch.py
    ```

1. Configure RViz

    * Display | Global Options | Fixed Frame = 'world'
    * Add | rviz_default_plugins | RobotModel
    * Add | moveit_ros_visualization | MotionPlanning