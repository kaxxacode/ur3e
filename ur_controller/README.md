# UR Controller


## Detecting towers

```BASH
python3 ~/code/ur3e/ur_controller/detect_towers.py --model ~/code/ur3e/ur_controller/best.pt
```


```bash
cat > ~/code/ur3e/moveit/NETWORK_SETUP.md << 'EOF'
# Network Setup Guide — UR3e Robot Connection

## Overview
The Ubuntu environment runs inside WSL2 on Windows. The ethernet connection
to the robot is via a USB ethernet dongle (D-Link DUB-1312) which must be
shared with WSL2 every session using usbipd.

---

## Step 1 — Attach USB Devices to WSL2 (Windows PowerShell as Administrator)

Open PowerShell as Administrator and run:

```powershell
usbipd attach --wsl --busid 1-3
```

This attaches the D-Link ethernet dongle. The RealSense camera should
already be attached (busid 2-13). If not, run:

```powershell
usbipd attach --wsl --busid 2-13
```

Verify both are attached:
```powershell
usbipd list
```
Both devices should show STATE = Attached.

---

## Step 2 — Configure Network in WSL2 Ubuntu

Open WSL2 Ubuntu terminal and run:

```bash
sudo ip link set enxc0a0bb58ca64 up
sudo ip addr add 192.168.1.10/24 dev enxc0a0bb58ca64
sudo ip route del 192.168.1.0/24 dev eth0
```

---

## Step 3 — Verify Connection

```bash
ping 192.168.1.102
```

You should get replies. If not, check:
- Robot controller is powered on
- Ethernet cable is plugged into the robot controller box
- Robot network settings on tablet are set to static IP 192.168.1.102

---

## Robot Network Settings (Polyscope Tablet)
```
Hamburger menu → Settings → Network
IP address:   192.168.1.102
Subnet mask:  255.255.255.0
Gateway:      192.168.1.1
Mode:         Static
```

---

## Step 4 — Verify Python Dependencies

```bash
python3 -c "import rtde_control; import rtde_receive; import scipy; import pyrealsense2; print('all ok')"
```

---

## Notes
- These steps must be repeated every session as WSL2 does not persist
  USB attachments or manual IP configurations across reboots.
- The ethernet interface name is enxc0a0bb58ca64 — this is fixed to the
  dongle's MAC address and will not change.
- If the route deletion command fails with "No such process" it means the
  route was not added yet — this is fine, continue to the ping step.
- Robot must be in Remote Control mode for script commands to work:
  Polyscope top bar → switch to Remote Control.

---

## Quick Reference — Every Session

```bash
# In PowerShell (Admin)
usbipd attach --wsl --busid 1-3
usbipd attach --wsl --busid 2-13

# In WSL2 Ubuntu
sudo ip link set enxc0a0bb58ca64 up
sudo ip addr add 192.168.1.10/24 dev enxc0a0bb58ca64
sudo ip route del 192.168.1.0/24 dev eth0
ping 192.168.1.102
```
EOF

echo "README created"
```

Run that in your WSL2 terminal and it will save the file to your workspace. Or if you want it as a proper downloadable file let me know and I'll generate it differently.