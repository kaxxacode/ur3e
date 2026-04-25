import torch

ckpt = torch.load("best.pt", map_location="cpu", weights_only=False)

# The 'version' key usually contains the software version (e.g., '8.3.0')
print("Software Version:", ckpt.get('version'))

# The 'model' key contains the architecture. 
# Looking at the class names inside can tell you if it's YOLOv8, v10, etc.
print("Model Architecture:", type(ckpt['model']))

# Version 8.x.x: This usually indicates YOLOv8 or YOLOv9.
# Version 8.3.x or higher: Often associated with YOLO11 (released late 2024).
# Version 8.4.x (or 2026 releases): Likely YOLO26, which introduced NMS-free