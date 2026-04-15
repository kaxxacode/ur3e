ARG ROS_DISTRO=jazzy
ARG DOCKER_IMAGE=main-jazzy-tutorial-source
FROM moveit/moveit2:${DOCKER_IMAGE}
SHELL ["/bin/bash", "-c"]
ENV ROS_DISTRO=${ROS_DISTRO}

RUN apt-get update && apt-get install -y \
    python3-vcstool \
    python3-pip \
    python3-opencv \
    ros-jazzy-realsense2-camera \
    ros-jazzy-cv-bridge \
    ros-jazzy-image-geometry \
    ros-jazzy-tf-transformations \
    ros-jazzy-message-filters

# Install AI and Math libraries
# We use --break-system-packages because this is a dedicated Docker container
RUN pip install --no-cache-dir --break-system-packages --ignore-installed \
    ultralytics \
    transforms3d

# Numpy downgrade 
RUN pip install --no-cache-dir --break-system-packages "numpy<2.0"

# Clone UR3 driver and dependencies
RUN mkdir -p /root/ws_moveit/src && cd /root/ws_moveit/src && \
    git clone -b ${ROS_DISTRO} https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver.git && \
    git clone https://github.com/UniversalRobots/Universal_Robots_Client_Library.git && \
    git clone https://github.com/ros-industrial/ur_msgs.git

# Install all dependencies
RUN apt-get update && \
    rosdep install -r --from-paths /root/ws_moveit/src --ignore-src --rosdistro ${ROS_DISTRO} -y

# Build workspace
WORKDIR /root/ws_moveit
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# Auto-source the workspace
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "source /root/ws_moveit/install/setup.bash" >> /root/.bashrc

ENTRYPOINT ["/bin/bash"]
