import pyrealsense2 as rs
import numpy as np
import cv2
import time
from ultralytics import YOLO
import rtde_control
import rtde_receive
import csv
import os

# ── Configuration ─────────────────────────────────────────────
ROBOT_IP = "192.168.1.102"
WEIGHTS  = "/home/user/ur_experiment/best.pt"

# Fixed orientation for all moves
ORI = [2.235, -2.201, 0.0]

# Home position
HOME = [81.0, -305.0, 383.0, 2.235, -2.201, 0.0]

# Observation X, Y (mm) — camera 0,0 above part 0,0
OBS_X = HOME[0]
OBS_Y = HOME[1]

# Part 0,0 in base frame (mm)
PART_ORIGIN = np.array([6.66, -306.01, 88.9])

# Known tower positions in base frame (mm)
TOWER_KNOWN_POS = {
    "12": np.array([-16.0, -287.5,  68.0]),
    "17": np.array([ 26.5, -287.5,  73.0]),
    "22": np.array([ -1.0, -322.5,  78.0]),
    "27": np.array([ 26.5, -322.5,  83.0]),
}

TOWERS = list(TOWER_KNOWN_POS.keys())

# Highest tower top Z in base frame (mm)
HIGHEST_TOP_Z = 83.0

# Test heights above highest tower (mm)
TEST_HEIGHTS = [100, 150, 200, 250, 300]

# Constants from camera holder and tool geometry (mm)
CAM_Z_OFFSET     = 15.0   # camera front glass is 15mm below flange
EXT_LENGTH       = 35.0   # extrusion tip is 35mm below flange
CAM_GLASS_OFFSET = 0.0037 # D405 optical centre is 3.7mm behind front glass (metres)
                          # SDK reports Z from front glass; X/Y back-projection needs
                          # Z from optical centre, so add this before back-projecting.

# X-axis tilt correction — measured from vision test with aluminium mount.
# Camera optical axis has a residual ~0.48deg tilt in the -X direction despite
# the machined bracket. This produces a systematic X error proportional to
# depth: approximately -0.0084 mm of X error per mm of camera-to-target depth.
# Subtracting this term from the back-projected X removes the height-dependent
# drift, leaving only a small constant residual.
TILT_X_SLOPE = +0.01138  # mm X-error per mm depth (positive = tilt in +X)

# Constant Error offsets observed from results
X_CONST_ERR = 0.0
Y_CONST_ERR = 0.0
Z_CONST_ERR = 1.5

# Speeds
SPEED      = 0.05
SPEED_HOME = 0.2
ACCEL      = 1.2

CONFIDENCE_THRESHOLD = 0.7

# ── Log file ──────────────────────────────────────────────────
LOG_FILE     = "/home/user/ur_experiment/vision_errors.csv"
write_header = not os.path.exists(LOG_FILE)

def log_result(height_mm, tower, det_x, det_y, det_z,
               known_x, known_y, known_z,
               cam_err_x, cam_err_y, cam_err_z):
    global write_header
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "height_mm", "tower",
                "det_x", "det_y", "det_z",
                "known_x", "known_y", "known_z",
                "cam_err_x", "cam_err_y", "cam_err_z",
                "timestamp"
            ])
            write_header = False
        writer.writerow([
            height_mm, tower,
            det_x, det_y, det_z,
            known_x, known_y, known_z,
            cam_err_x, cam_err_y, cam_err_z,
            time.strftime("%Y-%m-%d %H:%M:%S")
        ])

# ── Helper ────────────────────────────────────────────────────
def to_rtde_pose(pos_mm_rad):
    return [
        pos_mm_rad[0] / 1000,
        pos_mm_rad[1] / 1000,
        pos_mm_rad[2] / 1000,
        pos_mm_rad[3],
        pos_mm_rad[4],
        pos_mm_rad[5],
    ]

# ── Robot connection ──────────────────────────────────────────
print("Connecting to robot...")
rtde_c = rtde_control.RTDEControlInterface(ROBOT_IP)
rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
print("Connected.")

def move_to(pos_mm_rad, speed=SPEED):
    pose = to_rtde_pose(pos_mm_rad)
    rtde_c.moveL(pose, speed, ACCEL)

def go_home():
    print("  Moving to home...")
    move_to(HOME, speed=SPEED_HOME)

def get_tcp_z():
    pose = rtde_r.getActualTCPPose()
    return pose[2] * 1000

# ── Camera setup ──────────────────────────────────────────────
pipeline = rs.pipeline()
config   = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 5)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16,  5)
profile  = pipeline.start(config)

intr  = (profile.get_stream(rs.stream.color)
         .as_video_stream_profile().get_intrinsics())
align = rs.align(rs.stream.color)

print("[INFO] Flushing camera pipeline...")
for _ in range(30):
    pipeline.wait_for_frames()
print("[OK]  D405 streaming at 1280x720")

# ── YOLO ──────────────────────────────────────────────────────
print(f"[INFO] Loading model: {WEIGHTS}")
model = YOLO(WEIGHTS)
print(f"[OK]  Model loaded. Classes: {list(model.names.values())}")

# ── Live feed ─────────────────────────────────────────────────
def show_live_feed(duration=15):
    print("  Live feed — SPACE to continue, Q to skip height")
    start = time.time()
    while True:
        frames      = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        img       = np.asanyarray(color_frame.get_data())
        results   = model(img, verbose=False)[0]
        annotated = results.plot()
        n_det     = len(results.boxes)
        elapsed   = time.time() - start
        cv2.putText(annotated,
                    f"Detections: {n_det}  |  {elapsed:.1f}s / {duration}s",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated,
                    "SPACE = continue  |  Q = skip height",
                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        cv2.imshow("Live Detection", annotated)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            cv2.destroyAllWindows()
            return True
        elif key == ord('q'):
            cv2.destroyAllWindows()
            return False
        if elapsed > duration:
            cv2.destroyAllWindows()
            return True

# ── Tower detection ───────────────────────────────────────────
def flush_pipeline(n=10):
    for _ in range(n):
        pipeline.wait_for_frames()

def get_depth_at_pixel(depth_frame, cx, cy, window=5):
    depths = []
    for dx in range(-window, window + 1):
        for dy in range(-window, window + 1):
            px, py = cx + dx, cy + dy
            if 0 <= px < 1280 and 0 <= py < 720:
                d = depth_frame.get_distance(px, py)
                if d > 0:
                    depths.append(d)
    if len(depths) == 0:
        return 0
    return float(np.median(depths))


def detect_towers(n_frames=10):
    flush_pipeline()
    detections = {k: [] for k in TOWERS}

    valid_frames = 0
    attempts     = 0
    MAX_ATTEMPTS = 50
    while valid_frames < n_frames and attempts < MAX_ATTEMPTS:
        attempts += 1

        frames      = pipeline.wait_for_frames()
        frames      = align.process(frames)
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            continue
        img     = np.asanyarray(color_frame.get_data())
        results = model(img, verbose=False)[0]

        frame_data = {}
        for box in results.boxes:
            cls_name = model.names[int(box.cls)]
            if cls_name not in TOWERS:
                continue

            conf = float(box.conf[0])
            if conf < CONFIDENCE_THRESHOLD:
                continue

            cx = int((box.xyxy[0][0] + box.xyxy[0][2]) / 2)
            cy = int((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
            z  = get_depth_at_pixel(depth_frame, cx, cy, window=5)
            if z == 0:
                continue

            # X, Y back-projection uses optical-centre Z (glass + 3.7mm).
            # Z is kept as glass-referenced for the coordinate transform,
            # where CAM_Z_OFFSET is also measured to the front glass.
            z_optical = z + CAM_GLASS_OFFSET
            x = (cx - intr.ppx) * z_optical / intr.fx
            y = (cy - intr.ppy) * z_optical / intr.fy
            frame_data[cls_name] = [x, y, z]

        if set(frame_data.keys()) == set(TOWERS):
            for cls_name, pt in frame_data.items():
                detections[cls_name].append(pt)
            valid_frames += 1
        else:
            missing = set(TOWERS) - set(frame_data.keys())
            print(f"    Frame {attempts} rejected — missing: {missing}")

    if valid_frames < n_frames:
        print(f"    ERROR: only {valid_frames} complete frames after {MAX_ATTEMPTS} attempts — skipping height")
        return {}

    result = {}
    for cls_name, pts in detections.items():
        result[cls_name] = np.median(pts, axis=0)
        print(f"    {cls_name} camera frame: "
            f"x={result[cls_name][0]:.4f} "
            f"y={result[cls_name][1]:.4f} "
            f"z={result[cls_name][2]:.4f} metres")

    return result

def camera_to_base(pt_cam, tcp_z_mm):
    """
    Camera 0,0 is directly above part 0,0.
    X, Y from camera frame with Y flipped.
    Z from depth reading corrected for camera height and extrusion offset.
    A tilt correction is applied to X: the aluminium camera bracket has a
    residual ~0.48deg tilt in -X, measured from multi-height vision tests.
    This causes X error proportional to depth, corrected by subtracting
    TILT_X_SLOPE * depth_mm from the back-projected X.
    """
    # X error due to camera tilt, dependent on Z
    depth_mm = pt_cam[2] * 1000

    base_x = PART_ORIGIN[0] + pt_cam[0] * 1000 - TILT_X_SLOPE * depth_mm + X_CONST_ERR
    base_y = PART_ORIGIN[1] + (-pt_cam[1]) * 1000 + Y_CONST_ERR
    camera_z_mm = tcp_z_mm - CAM_Z_OFFSET
    base_z = camera_z_mm - pt_cam[2] * 1000 + EXT_LENGTH + Z_CONST_ERR
    return np.array([base_x, base_y, base_z])

# ── Main loop ─────────────────────────────────────────────────
print("\n" + "="*50)
print("  VISION ERROR CHARACTERISATION")
print(f"  Log: {LOG_FILE}")
print("="*50)

go_home()

for height in TEST_HEIGHTS:

    test_z = HIGHEST_TOP_Z + height - 20

    print(f"\n{'='*50}")
    print(f"Height: {height}mm above highest tower  (Z={test_z:.2f}mm)")
    print(f"{'='*50}")

    obs_pos = [OBS_X, OBS_Y, test_z, ORI[0], ORI[1], ORI[2]]
    move_to(obs_pos, speed=SPEED_HOME)
    time.sleep(2)

    if not show_live_feed(duration=15):
        print(f"  Height {height}mm skipped")
        go_home()
        continue

    tcp_z_mm = get_tcp_z()
    print(f"  TCP Z: {tcp_z_mm:.2f}mm")

    print("  Detecting towers...")
    tower_positions = detect_towers(n_frames=10)

    if not tower_positions:
        print(f"  No towers detected at {height}mm — skipping")
        go_home()
        continue

    for tower_name, pt_cam in tower_positions.items():
        pt_base_mm = camera_to_base(pt_cam, tcp_z_mm)

        if np.any(np.isnan(pt_base_mm)):
            print(f"  WARNING: NaN for {tower_name} — skipping")
            continue

        known_pos = TOWER_KNOWN_POS[tower_name]
        cam_err_x = pt_base_mm[0] - known_pos[0]
        cam_err_y = pt_base_mm[1] - known_pos[1]
        cam_err_z = pt_base_mm[2] - known_pos[2]

        print(f"\n  Tower {tower_name}mm")
        print(f"    Detected: X={pt_base_mm[0]:.2f} Y={pt_base_mm[1]:.2f} Z={pt_base_mm[2]:.2f} mm")
        print(f"    Known:    X={known_pos[0]:.2f} Y={known_pos[1]:.2f} Z={known_pos[2]:.2f} mm")
        print(f"    Error:    X={cam_err_x:.2f} Y={cam_err_y:.2f} Z={cam_err_z:.2f} mm")

        log_result(
            height, tower_name,
            pt_base_mm[0], pt_base_mm[1], pt_base_mm[2],
            known_pos[0], known_pos[1], known_pos[2],
            cam_err_x, cam_err_y, cam_err_z
        )

    input(f"\n  Height {height}mm complete — press ENTER when ready to move to next height...")
    go_home()

# ── Cleanup ───────────────────────────────────────────────────
rtde_c.disconnect()
rtde_r.disconnect()
pipeline.stop()
print("\nVision error test complete. Results saved to vision_errors.csv")
