"""
detect_towers.py
----------------
Runs YOLOv11 detection on the Intel RealSense D405 live feed.
Draws bounding boxes and class labels on the preview window.
Prints detections to the terminal.

Usage:
    python3 detect_towers.py --model /path/to/best.pt

Requirements:
    pip3 install ultralytics pyrealsense2 opencv-python

Press Q to quit.
"""

import argparse
import sys
import cv2
import numpy as np

try:
    import pyrealsense2 as rs
except ImportError:
    sys.exit("[ERROR] pyrealsense2 not found.\n        Run: pip3 install pyrealsense2")

try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("[ERROR] ultralytics not found.\n        Run: pip3 install ultralytics")

# ---------------------------------------------------------------------------
# Colours per class (BGR) — add more if you have more classes
# ---------------------------------------------------------------------------
CLASS_COLOURS = {
    "12":     (0,   255, 0),    # green
    "17":     (0,   165, 255),  # orange
    "22":     (255, 0,   0),    # blue
    "27":     (0,   0,   255),  # red
    "Center": (0,   255, 255),  # yellow
}
DEFAULT_COLOUR = (255, 255, 255)

CONFIDENCE_THRESHOLD = 0.5   # detections below this are ignored

# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="YOLOv11 tower detection on D405")
    parser.add_argument(
        "--model",
        type=str,
        default="best.pt",
        help="Path to YOLOv11 .pt weights file (default: best.pt in current directory)",
    )
    return parser.parse_args()


def start_camera():
    pipeline = rs.pipeline()
    cfg      = rs.config()
    cfg.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    pipeline.start(cfg)
    for _ in range(30):
        pipeline.wait_for_frames()
    print("[OK]  D405 streaming at 1280x720")
    return pipeline


def draw_detections(frame, results):
    """Draw bounding boxes and labels on the frame. Returns annotated frame."""
    detections = []

    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])
            if conf < CONFIDENCE_THRESHOLD:
                continue

            cls_id   = int(box.cls[0])
            cls_name = result.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            colour = CLASS_COLOURS.get(cls_name, DEFAULT_COLOUR)
            cx_box = (x1 + x2) // 2
            cy_box = (y1 + y2) // 2

            if cls_name == "Center":
                # Draw a crosshair and filled dot for the centre point
                cv2.line(frame, (cx_box - 20, cy_box), (cx_box + 20, cy_box), colour, 2)
                cv2.line(frame, (cx_box, cy_box - 20), (cx_box, cy_box + 20), colour, 2)
                cv2.circle(frame, (cx_box, cy_box), 5, colour, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 1)
            else:
                # Standard bounding box for all other classes
                cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)

            # Label background
            label     = f"{cls_name} {conf:.2f}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - lh - 8), (x1 + lw, y1), colour, -1)
            cv2.putText(frame, label, (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            detections.append({
                "class":      cls_name,
                "confidence": conf,
                "bbox":       (x1, y1, x2, y2),
                "centre":     (cx_box, cy_box),
            })

    return frame, detections


def main():
    args = parse_args()

    print(f"[INFO] Loading model: {args.model}")
    model = YOLO(args.model)
    print(f"[OK]  Model loaded. Classes: {list(model.names.values())}")

    pipeline = start_camera()
    print("\nRunning detection. Press Q to quit.\n")

    try:
        while True:
            frames = pipeline.wait_for_frames()
            colour = frames.get_color_frame()
            if not colour:
                continue

            frame   = np.asanyarray(colour.get_data())
            results = model(frame, verbose=False)

            annotated, detections = draw_detections(frame.copy(), results)

            # Print detections to terminal
            if detections:
                for d in detections:
                    cx, cy = d["centre"]
                    print(
                        f"  {d['class']:<10}  conf={d['confidence']:.2f}"
                        f"  centre=({cx}, {cy})"
                    )
                print()

            # Overlay instruction
            cv2.putText(annotated, "Q = quit",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("YOLOv11 Tower Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        print("Stopped.")


if __name__ == "__main__":
    main()