"""
download_model.py
-----------------
Downloads the trained YOLOv11 weights from Roboflow to your local machine.
 
Usage:
    python3 download_model.py
 
Requirements:
    pip3 install roboflow
 
The weights file (best.pt) will be saved in the current directory.
"""
 
from roboflow import Roboflow
 
# ---------------------------------------------------------------------------
# Fill in your details before running
# ---------------------------------------------------------------------------
 
API_KEY      = "jx94iZyNPmqHjKcKSCGW"   # Roboflow → Settings → Roboflow API
WORKSPACE    = "towerdetection" # Roboflow → Settings → Workspace (slug)
PROJECT_NAME = "testtower-4p8p8"
VERSION      = 20
 
# ---------------------------------------------------------------------------
 
rf      = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE).project(PROJECT_NAME)
version = project.version(VERSION)
 
print(f"Downloading YOLOv11 weights for {PROJECT_NAME} v{VERSION} ...")
version.download("yolov11")
print("Done. Weights saved in the current directory.")