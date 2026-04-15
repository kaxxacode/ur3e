# Camera Fix

## Problem Summary

I still cannot get the RealSense D405 camera to work with any 
of the Docker Containers on this computer.

This camera was working until I decided to recreate the container 
with changes to allow the container to access a UR3e robot.

I reverted the code to my previous Docker creation files, created 
the old container but this is not working anymore either.

I now have two containers one with the settings when the camera was 
working and one with the changes to get the robot connectivity
named as follows:

* `camera_last_working_container` - container using files that had the camera working
* `moveit2_ur3_v2_container` - container with updates for robot access

Keep in mind that none of these are working today.


### Details

I want to provide you with the files for camera_last_working_container. 
Let's see if we can get this to work again. Attached find Dockerfile, 
docker-compose.yml and setup_ur3.sh

The docker image was created using:

```bash
docker build  -t camera_last_working  .
```

The docker container was created using:

```bash
./setup_ur3.sh
```

My assumption is that we made changes in the stack that broke the camera connection.


### Software stack

* Windows 10 (IP: 192.168.0.127, Subnet: 192.168.0.x)
* WSL2 Ubuntu 22.04
* Docker container with Ubuntu 24.04 (running moveit)


### Reproducing the Problem

1. On Windows, from powershell, ran the following:

> attach --wsl --busid 2-13

```TEXT
usbipd: info: Using WSL distribution 'Ubuntu-22.04' to attach; the device will be available in all WSL 2 distributions.
usbipd: info: Detected networking mode 'nat'.
usbipd: info: Using IP address 172.30.0.1 to reach the host.
```

> usbipd list

```TEXT
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
2-9    06cb:00c9  Synaptics UWP WBDI                                            Not shared
2-10   8087:0026  Intel(R) Wireless Bluetooth(R)                                Not shared
2-13   8086:0b5b  Intel(R) RealSense(TM) Depth Camera 405  Depth                Attached

Persisted:
GUID                                  DEVICE
140ae816-024e-496e-a1fb-222e35888065  Intel(R) RealSense(TM) Depth Camera 405  Depth
d488284e-0a38-49ca-bde6-95bcba9c5d3d  Intel(R) RealSense(TM) Depth Camera 405  Depth
f28fe7e6-e6d2-43c7-9658-ac03bc8feec9  D-Link DUB-1312
```

2. In Docker camera_last_working_container run the following:

> lsusb

```TEXT
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 002 Device 003: ID 8086:0b5b Intel Corp. Intel(R) RealSense(TM) Depth Camera 405
```

> ros2 launch realsense2_camera rs_launch.py \
        camera_name:=camera \
        align_depth.enable:=true \
        pointcloud.enable:=true \
        rgb_camera.profile:=640x480x15 \
        depth_module.profile:=640x480x15 \
        filters:=spatial,temporal

```TEXT
[INFO] [launch]: All log files can be found below /root/.ros/log/2026-04-12-11-04-11-928270-docker-desktop-84
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: 🚀 Launching as Normal ROS Node
[INFO] [realsense2_camera_node-1]: process started with pid [89]
[realsense2_camera_node-1] [INFO] [1775991852.389136343] [camera.camera]: RealSense ROS v4.56.4
[realsense2_camera_node-1] [INFO] [1775991852.389236049] [camera.camera]: Built with LibRealSense v2.56.4
[realsense2_camera_node-1] [INFO] [1775991852.389264751] [camera.camera]: Running with LibRealSense v2.56.4
[realsense2_camera_node-1] [WARN] [1775991852.391675905] [camera.camera]: No RealSense devices were found!
[realsense2_camera_node-1] [WARN] [1775991858.393740542] [camera.camera]: No RealSense devices were found!
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[realsense2_camera_node-1] [INFO] [1775991861.560752531] [rclcpp]: signal_handler(signum=2)
[INFO] [realsense2_camera_node-1]: process has finished cleanly [pid 89]
```

### Goal


I would like to get the camera to work on camera_last_working_container


---

## FIX

Looking at the full picture — the Dockerfile, compose file, setup script, and 
the symptom (lsusb sees the device inside the container but librealsense says 
"No RealSense devices were found") — this is a classic WSL2 + Docker USB passthrough 
issue.

The key clue is that lsusb works inside the container (USB bus passthrough is fine) 
but librealsense still can't find the camera. This almost always means the /dev/video* 
and /dev/media* device nodes are missing inside the container.

Test run this in WSL2:

```BASH
ls /dev/video* /dev/media*
```

```TEXT
ls: cannot access '/dev/video*': No such file or directory
ls: cannot access '/dev/media*': No such file or directory
```

This confirms the problem is upstream of Docker entirely — the WSL2 kernel isn't creating 
the V4L2 device nodes when the camera is attached. Since it was working before, the 
uvcvideo kernel module likely got unloaded or something broke its auto-loading.


Check if the uvcvideo module is loaded or even available:
```BASH
lsmod | grep uvc
modinfo uvcvideo
```

returns...

```TEXT
filename:       /lib/modules/6.6.87.2-microsoft-standard-WSL2/kernel/drivers/media/usb/uvc/uvcvideo.ko
version:        1.1.1
license:        GPL
description:    USB Video Class driver
author:         Laurent Pinchart <laurent.pinchart@ideasonboard.com>
srcversion:     46B361D0F4B63589DF30215
alias:          usb:v*p*d*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v*p*d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p1155d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0B5Cd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0B5Bd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0B3Ad*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0B07d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0B03d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0AD4d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0AD3d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v8086p0AD2d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v5986p1180d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v5986p1172d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v3277p0072d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v30C9p0093d*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v2E1Ap4C01d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v2B7EpB752d*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v29FEp4D53d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v2833p0211d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v2833p0201d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v1FC9p009Bd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v1C4Fp3000d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v1BCFp0B40d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v1B3Fp2002d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v1B3Bp2951d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v19ABp1000d00*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v19ABp1000d01[0-1]*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v19ABp1000d012[0-6]dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v199Ep8102d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v18ECp3290d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v18ECp3288d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v18ECp3188d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v18CDpCAFEd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v1871p0516d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v1871p0306d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v17EFp480Bd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v17DCp0202d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v174Fp8A34d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v174Fp8A33d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v174Fp8A31d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v174Fp8A12d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v174Fp5931d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v174Fp5212d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v16D0p0ED1d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v152Dp0310d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v13D3p5103d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0E8Dp0004d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0C45p6366d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0BD3p0555d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0AC8p3420d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0AC8p3410d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0AC8p332Dd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v06F8p300Cd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05E3p0505d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05C8p0403d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05ACp8600d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05ACp8514d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05ACp8501d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05A9p7670d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05A9p264Ad*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05A9p2643d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05A9p2641d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v05A9p2640d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v058Fp3820d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v04F2pB746d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v04F2pB6BAd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v04F2pB67Cd*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v04F2pB5EBd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v04F2pB071d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp08D3d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp089Bd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp087Cd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp085Cd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp082Dd*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp08C7d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v046Dp08C6d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v046Dp08C5d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v046Dp08C3d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v046Dp08C2d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v046Dp08C1d*dc*dsc*dp*icFFisc01ip00in*
alias:          usb:v046Dp0823d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v046Dp0821d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v045Ep0723d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v045Ep0721d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v045Ep00F8d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0458p706Ed*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0416pA91Ad*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0408p4035d*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v0408p4033d*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v0408p4034d*dc*dsc*dp*ic0Eisc01ip01in*
alias:          usb:v0408p4030d*dc*dsc*dp*ic0Eisc01ip00in*
alias:          usb:v0408p3090d*dc*dsc*dp*ic0Eisc01ip00in*
depends:        usbcore,videobuf2-common,videodev,mc,videobuf2-v4l2,videobuf2-vmalloc,usb-common,uvc
retpoline:      Y
intree:         Y
name:           uvcvideo
vermagic:       6.6.87.2-microsoft-standard-WSL2 SMP preempt mod_unload modversions
parm:           clock:Video buffers timestamp clock
parm:           hwtimestamps:Use hardware timestamps (uint)
parm:           nodrop:Don't drop incomplete frames (uint)
parm:           quirks:Forced device quirks (uint)
parm:           trace:Trace level bitmask (uint)
parm:           timeout:Streaming control requests timeout (uint)
```

Good news — the module exists and even has explicit aliases for the D405 (v8086p0B5B). 
It's just not loaded. Let's load it now:

```BASH
sudo modprobe uvcvideo
```

Reattach camera from powershell:

```bash
usbipd detach --all
usbipd attach --wsl --busid 2-13
usbipd list
```

On WSL2 confirm the video and media folders are present:

```bash
ls /dev/video* /dev/media*
```

```TEXT
/dev/media0  /dev/video0  /dev/video1  /dev/video2  /dev/video3  /dev/video4  /dev/video5
```

Restart container and check camera access:

```bash
rs-enumerate-devices
```

returns

```TEXT
Device info:
    Name                          :     Intel RealSense D405
    Serial Number                 :     335122270357
    Firmware Version              :     5.17.0.10
    Recommended Firmware Version  :     5.17.0.9
    Physical Port                 :     /sys/devices/platform/vhci_hcd.0/usb2/2-1/2-1:1.0/video4linux/video0
    Debug Op Code                 :     15
    Advanced Mode                 :     YES
    Product Id                    :     0B5B
    Camera Locked                 :     YES
    Usb Type Descriptor           :     3.2
    Product Line                  :     D400
    Asic Serial Number            :     315423070564
    Firmware Update Id            :     315423070564
    Dfu Device Path               :
    Connection Type               :     USB

Stream Profiles supported by Stereo Module
 Supported modes:
    STREAM      RESOLUTION     FORMAT      FPS
    Infrared    1280x720       UYVY        @ 30/15/5 Hz
    Infrared        |          BGRA8       @ 30/15/5 Hz
    Infrared        |          RGBA8       @ 30/15/5 Hz
    Infrared        |          BGR8        @ 30/15/5 Hz
    Infrared        |          RGB8        @ 30/15/5 Hz
    Infrared     848x480       UYVY        @ 90/60/30/15/5 Hz
    Infrared        |          BGRA8       @ 90/60/30/15/5 Hz
    Infrared        |          RGBA8       @ 90/60/30/15/5 Hz
    Infrared        |          BGR8        @ 90/60/30/15/5 Hz
    Infrared        |          RGB8        @ 90/60/30/15/5 Hz
    Infrared     640x480       UYVY        @ 90/60/30/15/5 Hz
    Infrared        |          BGRA8       @ 90/60/30/15/5 Hz
    Infrared        |          RGBA8       @ 90/60/30/15/5 Hz
    Infrared        |          BGR8        @ 90/60/30/15/5 Hz
    Infrared        |          RGB8        @ 90/60/30/15/5 Hz
    Infrared     640x360       UYVY        @ 90/60/30/15/5 Hz
    Infrared        |          BGRA8       @ 90/60/30/15/5 Hz
    Infrared        |          RGBA8       @ 90/60/30/15/5 Hz
    Infrared        |          BGR8        @ 90/60/30/15/5 Hz
    Infrared        |          RGB8        @ 90/60/30/15/5 Hz
    Infrared     480x270       UYVY        @ 90/60/30/15/5 Hz
    Infrared        |          BGRA8       @ 90/60/30/15/5 Hz
    Infrared        |          RGBA8       @ 90/60/30/15/5 Hz
    Infrared        |          BGR8        @ 90/60/30/15/5 Hz
    Infrared        |          RGB8        @ 90/60/30/15/5 Hz
    Infrared     424x240       UYVY        @ 90/60/30/15/5 Hz
    Infrared        |          BGRA8       @ 90/60/30/15/5 Hz
    Infrared        |          RGBA8       @ 90/60/30/15/5 Hz
    Infrared        |          BGR8        @ 90/60/30/15/5 Hz
    Infrared        |          RGB8        @ 90/60/30/15/5 Hz
    Infrared 1  1288x808       Y16         @ 25/15 Hz
    Infrared 1  1280x720       Y8          @ 30/15/5 Hz
    Infrared 1   848x480       Y8          @ 90/60/30/15/5 Hz
    Infrared 1   640x480       Y8          @ 90/60/30/15/5 Hz
    Infrared 1   640x360       Y8          @ 90/60/30/15/5 Hz
    Infrared 1   480x270       Y8          @ 90/60/30/15/5 Hz
    Infrared 1   424x240       Y8          @ 90/60/30/15/5 Hz
    Infrared 2  1288x808       Y16         @ 25/15 Hz
    Infrared 2  1280x720       Y8          @ 30/15/5 Hz
    Infrared 2   848x480       Y8          @ 90/60/30/15/5 Hz
    Infrared 2   640x480       Y8          @ 90/60/30/15/5 Hz
    Infrared 2   640x360       Y8          @ 90/60/30/15/5 Hz
    Infrared 2   480x270       Y8          @ 90/60/30/15/5 Hz
    Infrared 2   424x240       Y8          @ 90/60/30/15/5 Hz
    Color       1280x720       RGB8        @ 30/15/5 Hz
    Color           |          Y8          @ 30/15/5 Hz
    Color           |          BGRA8       @ 30/15/5 Hz
    Color           |          RGBA8       @ 30/15/5 Hz
    Color           |          BGR8        @ 30/15/5 Hz
    Color           |          YUYV        @ 30/15/5 Hz
    Color        848x480       RGB8        @ 90/60/30/15/5 Hz
    Color           |          Y8          @ 90/60/30/15/5 Hz
    Color           |          BGRA8       @ 90/60/30/15/5 Hz
    Color           |          RGBA8       @ 90/60/30/15/5 Hz
    Color           |          BGR8        @ 90/60/30/15/5 Hz
    Color           |          YUYV        @ 90/60/30/15/5 Hz
    Color        640x480       RGB8        @ 90/60/30/15/5 Hz
    Color           |          Y8          @ 90/60/30/15/5 Hz
    Color           |          BGRA8       @ 90/60/30/15/5 Hz
    Color           |          RGBA8       @ 90/60/30/15/5 Hz
    Color           |          BGR8        @ 90/60/30/15/5 Hz
    Color           |          YUYV        @ 90/60/30/15/5 Hz
    Color        640x360       RGB8        @ 90/60/30/15/5 Hz
    Color           |          Y8          @ 90/60/30/15/5 Hz
    Color           |          BGRA8       @ 90/60/30/15/5 Hz
    Color           |          RGBA8       @ 90/60/30/15/5 Hz
    Color           |          BGR8        @ 90/60/30/15/5 Hz
    Color           |          YUYV        @ 90/60/30/15/5 Hz
    Color        480x270       RGB8        @ 90/60/30/15/5 Hz
    Color           |          Y8          @ 90/60/30/15/5 Hz
    Color           |          BGRA8       @ 90/60/30/15/5 Hz
    Color           |          RGBA8       @ 90/60/30/15/5 Hz
    Color           |          BGR8        @ 90/60/30/15/5 Hz
    Color           |          YUYV        @ 90/60/30/15/5 Hz
    Color        424x240       RGB8        @ 90/60/30/15/5 Hz
    Color           |          Y8          @ 90/60/30/15/5 Hz
    Color           |          BGRA8       @ 90/60/30/15/5 Hz
    Color           |          RGBA8       @ 90/60/30/15/5 Hz
    Color           |          BGR8        @ 90/60/30/15/5 Hz
    Color           |          YUYV        @ 90/60/30/15/5 Hz
    Depth       1280x720       Z16         @ 30/15/5 Hz
    Depth        848x480       Z16         @ 90/60/30/15/5 Hz
    Depth        640x480       Z16         @ 90/60/30/15/5 Hz
    Depth        640x360       Z16         @ 90/60/30/15/5 Hz
    Depth        480x270       Z16         @ 90/60/30/15/5 Hz
    Depth        424x240       Z16         @ 90/60/30/15/5 Hz
    Depth        256x144       Z16         @ 90 Hz
```

start camera node:

```bash
 ros2 launch realsense2_camera rs_launch.py \
        camera_name:=camera \
        align_depth.enable:=true \
        pointcloud.enable:=true \
        rgb_camera.profile:=640x480x15 \
        depth_module.profile:=640x480x15 \
        filters:=spatial,temporal
```

success return:

```text
[INFO] [launch]: All log files can be found below /root/.ros/log/2026-04-12-11-43-37-947177-docker-desktop-91
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: 🚀 Launching as Normal ROS Node
[INFO] [realsense2_camera_node-1]: process started with pid [96]
[realsense2_camera_node-1] [INFO] [1775994218.447637566] [camera.camera]: RealSense ROS v4.56.4
[realsense2_camera_node-1] [INFO] [1775994218.447744468] [camera.camera]: Built with LibRealSense v2.56.4
[realsense2_camera_node-1] [INFO] [1775994218.447769969] [camera.camera]: Running with LibRealSense v2.56.4
[realsense2_camera_node-1] [INFO] [1775994218.466489891] [camera.camera]: Device with serial number 335122270357 was found.
[realsense2_camera_node-1]
[realsense2_camera_node-1] [INFO] [1775994218.466570793] [camera.camera]: Device with physical ID /sys/devices/platform/vhci_hcd.0/usb2/2-1/2-1:1.0/video4linux/video0 was found.
[realsense2_camera_node-1] [INFO] [1775994218.466602394] [camera.camera]: Device with name Intel RealSense D405 was found.
[realsense2_camera_node-1] [INFO] [1775994218.466787698] [camera.camera]: Device with port number 2-1 was found.
[realsense2_camera_node-1] [INFO] [1775994218.466819699] [camera.camera]: Device USB type: 3.2
[realsense2_camera_node-1] [INFO] [1775994218.467208507] [camera.camera]: getParameters...
[realsense2_camera_node-1] [INFO] [1775994218.467703918] [camera.camera]: JSON file is not provided
[realsense2_camera_node-1] [INFO] [1775994218.467736019] [camera.camera]: Device Name: Intel RealSense D405
[realsense2_camera_node-1] [INFO] [1775994218.467763520] [camera.camera]: Device Serial No: 335122270357
[realsense2_camera_node-1] [INFO] [1775994218.467789320] [camera.camera]: Device physical port: /sys/devices/platform/vhci_hcd.0/usb2/2-1/2-1:1.0/video4linux/video0
[realsense2_camera_node-1] [INFO] [1775994218.467796321] [camera.camera]: Device FW version: 5.17.0.10
[realsense2_camera_node-1] [INFO] [1775994218.467800021] [camera.camera]: Device Product ID: 0x0B5B
[realsense2_camera_node-1] [INFO] [1775994218.467820621] [camera.camera]: Sync Mode: Off
[realsense2_camera_node-1] [INFO] [1775994218.653711516] [camera.camera]: Set ROS param depth_module.depth_profile to default: 848x480x30
[realsense2_camera_node-1] [INFO] [1775994218.654051023] [camera.camera]: Set ROS param depth_module.color_profile to default: 848x480x30
[realsense2_camera_node-1] [INFO] [1775994218.654514134] [camera.camera]: Set ROS param depth_module.infra_profile to default: 848x480x30
[realsense2_camera_node-1] [INFO] [1775994218.686870264] [camera.camera]: Stopping Sensor: Depth Module
[realsense2_camera_node-1] [INFO] [1775994218.704658165] [camera.camera]: Starting Sensor: Depth Module
[realsense2_camera_node-1] [INFO] [1775994218.717605657] [camera.camera]: Open profile: stream_type: Color(0), Format: RGB8, Width: 848, Height: 480, FPS: 30
[realsense2_camera_node-1] [INFO] [1775994218.717694059] [camera.camera]: Open profile: stream_type: Depth(0), Format: Z16, Width: 848, Height: 480, FPS: 30
[realsense2_camera_node-1] [INFO] [1775994218.731928480] [camera.camera]: RealSense Node Is Up!
```

## Restart Problem

The correct way is to use the WSL2 boot command in /etc/wsl.conf:

```BASH
echo -e '[boot]\ncommand=modprobe uvcvideo' | sudo tee -a /etc/wsl.conf
```

Shutdown wsl from powershell and try again:

```bash
wsl --shutdown
```

from wsl2:

```bash
lsmod | grep uvc
```

...returned:

```text
uvcvideo              114688  0
uvc                    12288  1 uvcvideo
videobuf2_vmalloc      16384  1 uvcvideo
videobuf2_v4l2         32768  1 uvcvideo
videodev              270336  2 videobuf2_v4l2,uvcvideo
videobuf2_common       57344  4 videobuf2_vmalloc,videobuf2_v4l2,uvcvideo,videobuf2_memops
mc                     65536  4 videodev,videobuf2_v4l2,uvcvideo,videobuf2_common
usbcore               290816  1 uvcvideo
usb_common             12288  2 usbcore,uvcvideo
```

from powershell:

```bash
usbipd attach --wsl --busid 2-13
```

from wsl2:

```bash
ls /dev/video* /dev/media*
```