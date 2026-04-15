"""
capture_images.py
-----------------
Automatically captures 1000 images from the Intel RealSense D405 at 5 photos
per second. Move the robot manually while this runs.

Press Q at any time to stop early.

Usage:
    python3 capture_images.py

Requirements:
    pip install pyrealsense2 opencv-python --break-system-packages

Images saved to: ~/dataset/images/
"""

import os
import sys
import time

import cv2
import numpy as np

try:
    import pyrealsense2 as rs
except ImportError:
    sys.exit(
        "[ERROR] pyrealsense2 not found.\n"
        "        Run: pip install pyrealsense2 --break-system-packages"
    )

OUTPUT_DIR  = os.path.expanduser("~/code/ur3e/ur_controller/dataset/images")
TARGET      = 300    # total images to capture
INTERVAL_S  = 0.2     # seconds between captures (0.2 = 5 per second)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pipeline = rs.pipeline()
    cfg      = rs.config()
    cfg.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    pipeline.start(cfg)

    # Let auto-exposure settle
    print("Starting camera, please wait...")
    for _ in range(30):
        pipeline.wait_for_frames()

    print(f"\nCapturing {TARGET} images at 5 per second.")
    print(f"Saving to: {OUTPUT_DIR}")
    print("Move the robot now. Press Q to stop early.\n")

    count       = 0
    last_save   = time.time()
    start_time  = time.time()

    try:
        while count < TARGET:
            frames = pipeline.wait_for_frames()
            colour = frames.get_color_frame()
            if not colour:
                continue

            img = np.asanyarray(colour.get_data())
            now = time.time()

            # Save at the target interval
            if now - last_save >= INTERVAL_S:
                count   += 1
                filename = os.path.join(OUTPUT_DIR, f"image_{count:04d}.png")
                cv2.imwrite(filename, img)
                last_save = now

            # Overlay progress on preview
            elapsed     = now - start_time
            remaining_s = max(0, (TARGET - count) * INTERVAL_S)
            display     = img.copy()
            cv2.putText(display,
                        f"Saved: {count}/{TARGET}   "
                        f"Elapsed: {int(elapsed)}s   "
                        f"Remaining: ~{int(remaining_s)}s",
                        (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 0), 2)

            # Progress bar
            bar_w = int((count / TARGET) * display.shape[1])
            cv2.rectangle(display, (0, display.shape[0] - 12),
                          (bar_w, display.shape[0]), (0, 255, 0), -1)

            cv2.imshow("D405 - Auto Capture", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                print("\nStopped early by user.")
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        total_time = time.time() - start_time
        print(f"\nDone -- {count} images saved to {OUTPUT_DIR}")
        print(f"Total time: {int(total_time // 60)}m {int(total_time % 60)}s")

if __name__ == "__main__":
    main()