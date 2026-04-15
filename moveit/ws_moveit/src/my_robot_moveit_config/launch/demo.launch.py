import os
import xacro
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    try:
        with open(absolute_file_path, 'r') as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        return None

def generate_launch_description():
    # 1. Path Setup
    # It is recommended to use get_package_share_directory instead of hardcoded /root/ paths
    description_pkg = "my_robot_description"
    config_pkg = "my_robot_moveit_config"
    
    urdf_path = os.path.join(get_package_share_directory(description_pkg), "urdf", "ur3e_setup.urdf.xacro")
    srdf_path = os.path.join(get_package_share_directory(config_pkg), "config", "ur3e_with_vision.srdf")
    
    # 2. Process Robot Description (URDF)
    robot_description_config = xacro.process_file(urdf_path)
    robot_description = {"robot_description": robot_description_config.toxml()}

    # 3. Process Semantic Description (SRDF)
    with open(srdf_path, 'r') as f:
        semantic_config = f.read()
    robot_description_semantic = {"robot_description_semantic": semantic_config}

    # 4. Load Kinematics and Controllers
    # These resolve the "No kinematics plugins defined" and "Controller manager not specified" errors
    kinematics_yaml = load_yaml(config_pkg, "config/kinematics.yaml")
    robot_description_kinematics = {"robot_description_kinematics": kinematics_yaml}
    
    controllers_yaml = load_yaml(config_pkg, "config/moveit_controllers.yaml")
    moveit_controllers = {
        "moveit_simple_controller_manager": controllers_yaml["moveit_simple_controller_manager"],
        "moveit_controller_manager": controllers_yaml["moveit_controller_manager"],
    }

    # 5. Planning Pipeline Configuration
    planning_pipeline_config = {
        "default_planning_pipeline": "ompl",
        "planning_pipelines": ["ompl"],
        "ompl": {
            "planning_plugins": ["ompl_interface/OMPLPlanner"],
            "request_adapters": [
                "default_planning_request_adapters/ResolveConstraintFrames",
                "default_planning_request_adapters/ValidateWorkspaceBounds",
                "default_planning_request_adapters/CheckStartStateBounds",
                "default_planning_request_adapters/CheckStartStateCollision",
            ],
            "response_adapters": [
                "default_planning_response_adapters/AddTimeOptimalParameterization",
                "default_planning_response_adapters/ValidateSolution",
            ],
        },
    }

    # 6. Sensors Configuration (3D Perception)
    sensors_path = os.path.join(get_package_share_directory(config_pkg), "config", "sensors_3d.yaml")

    # 7. Define Nodes
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            moveit_controllers,
            sensors_path,
            planning_pipeline_config,
            {"publish_robot_description_semantic": True},
            {"start_scene_monitor": True},
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
        ],
    )

    joint_state_publisher = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher,
        move_group_node,
        rviz_node,
    ])