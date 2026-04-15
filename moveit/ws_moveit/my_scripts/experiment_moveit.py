import pyrealsense2 as rs
import numpy as np
import cv2
import time
import csv
import os
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest, Constraints,
    PositionConstraint, OrientationConstraint, BoundingVolume,
)
from geometry_msgs.msg import PoseStamped, Vector3
from shape_msgs.msg import SolidPrimitive
from ultralytics import YOLO

# ── Configuration ─────────────────────────────────────────────
PLATFORM = "MoveIt2"
WEIGHTS  = "/root/ws_moveit/best.pt"
N_TRIALS = 20

# Fixed orientation (quaternion x y z w)
ORI_QUAT = [0.7126, -0.7017, 0.00574, 0.00898]  # x y z w

# Positions in mm
HOME_MM        = [81.0,    -305.0,  383.0]
APPROACH_XY_MM = [114.31,  -261.46,  93.41]
SAFE_Z_MM      = [109.43,  -255.09, 268.02]
APPROACH_Z_MM  = [219.96,  -335.28, 239.23]
PROBE_X_MM     = [142.78,  -261.45,  93.42]
PROBE_Y_MM     = [114.31,  -276.97,  93.40]
PROBE_Z_MM     = [219.97,  -335.28, 216.91]

KNOWN_PROBE_X = np.array([142.78, -261.45,  93.42])
KNOWN_PROBE_Y = np.array([114.31, -276.97,  93.40])
KNOWN_PROBE_Z = np.array([219.97, -335.28, 216.91])

PART_ORIGIN = np.array([9.0, -305.0, 88.9])

TOWER_KNOWN_POS = {
    "12": np.array([-16.0, -287.5, 68.0]),
    "17": np.array([ 26.5, -287.5, 73.0]),
    "22": np.array([ -1.0, -322.5, 78.0]),
    "27": np.array([ 26.5, -322.5, 83.0]),
}
TOWERS = list(TOWER_KNOWN_POS.keys())

OBS_X        = 81.0
OBS_Y        = -305.0
OBS_Z_MM     = 183.0
CAM_Z_OFFSET = 15.0
EXT_LENGTH   = 35.0

# Retry settings
MAX_RETRIES  = 10
RETRY_WAIT_S = 20.0

# ── Detection settings (matching detect_towers.py) ────────────
CONFIDENCE_THRESHOLD = 0.5
CLASS_COLOURS = {
    "12":     (0,   255, 0),
    "17":     (0,   165, 255),
    "22":     (255, 0,   0),
    "27":     (0,   0,   255),
    "Center": (0,   255, 255),
}
DEFAULT_COLOUR = (255, 255, 255)

# ── Log file ──────────────────────────────────────────────────
LOG_FILE     = "/root/ws_moveit/my_scripts/results_moveit.csv"
write_header = not os.path.exists(LOG_FILE)

def log_result(trial, tower, axis, error_mm, detected_pos, commanded):
    global write_header
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "platform", "trial", "tower", "axis", "error_mm",
                "det_x", "det_y", "det_z",
                "cmd_x", "cmd_y", "cmd_z", "timestamp"
            ])
            write_header = False
        writer.writerow([
            PLATFORM, trial, tower, axis, error_mm,
            detected_pos[0], detected_pos[1], detected_pos[2],
            commanded[0], commanded[1], commanded[2],
            time.strftime("%Y-%m-%d %H:%M:%S")
        ])


# ── MoveIt 2 Node ─────────────────────────────────────────────
class MoveItController(Node):
    def __init__(self):
        super().__init__("experiment_moveit")
        self._action_client = ActionClient(self, MoveGroup, "/move_action")
        self._tcp_pose = None

        self.create_subscription(
            PoseStamped,
            "/tcp_pose_broadcaster/pose",
            self._tcp_cb,
            10
        )

        self.get_logger().info("Waiting for MoveGroup action server...")
        self._action_client.wait_for_server()
        self.get_logger().info("MoveGroup action server ready.")

    def _tcp_cb(self, msg):
        self._tcp_pose = msg

    def get_tcp_z(self):
        rclpy.spin_once(self, timeout_sec=1.0)
        if self._tcp_pose is not None:
            z_mm = self._tcp_pose.pose.position.z * 1000.0
            self.get_logger().info(f"  TCP Z: {z_mm:.2f} mm")
            return z_mm
        self.get_logger().warn("  TCP pose not available — using fallback OBS_Z_MM")
        return OBS_Z_MM

    def _build_request(self, x_m, y_m, z_m, max_velocity_scaling=0.1):
        req = MotionPlanRequest()
        req.group_name = "ur_manipulator"
        req.num_planning_attempts = 5
        req.allowed_planning_time = 10.0
        req.max_velocity_scaling_factor = max_velocity_scaling
        req.max_acceleration_scaling_factor = 0.1

        target = PoseStamped()
        target.header.frame_id = "base"
        target.pose.position.x = x_m
        target.pose.position.y = y_m
        target.pose.position.z = z_m
        target.pose.orientation.x = ORI_QUAT[0]
        target.pose.orientation.y = ORI_QUAT[1]
        target.pose.orientation.z = ORI_QUAT[2]
        target.pose.orientation.w = ORI_QUAT[3]

        pos_con = PositionConstraint()
        pos_con.header.frame_id = "base"
        pos_con.link_name = "tool0"
        pos_con.target_point_offset = Vector3(x=0.0, y=0.0, z=0.0)
        bv = BoundingVolume()
        sp = SolidPrimitive()
        sp.type = SolidPrimitive.SPHERE
        sp.dimensions = [0.001]
        bv.primitives = [sp]
        bv.primitive_poses = [target.pose]
        pos_con.constraint_region = bv
        pos_con.weight = 1.0

        ori_con = OrientationConstraint()
        ori_con.header.frame_id = "base"
        ori_con.link_name = "tool0"
        ori_con.orientation = target.pose.orientation
        ori_con.absolute_x_axis_tolerance = 0.01
        ori_con.absolute_y_axis_tolerance = 0.01
        ori_con.absolute_z_axis_tolerance = 0.01
        ori_con.weight = 1.0

        goal_con = Constraints()
        goal_con.position_constraints = [pos_con]
        goal_con.orientation_constraints = [ori_con]
        req.goal_constraints = [goal_con]

        return req

    def move_to_mm(self, pos_mm, speed_scale=0.1):
        """Move to position in mm with automatic retry on driver drop."""
        x_m, y_m, z_m = [p / 1000.0 for p in pos_mm]

        for attempt in range(1, MAX_RETRIES + 1):
            self.get_logger().info(
                f"  Moving to X={pos_mm[0]:.2f} Y={pos_mm[1]:.2f} Z={pos_mm[2]:.2f} mm"
                + (f" (attempt {attempt}/{MAX_RETRIES})" if attempt > 1 else "")
            )

            try:
                req = self._build_request(x_m, y_m, z_m, max_velocity_scaling=speed_scale)
                goal = MoveGroup.Goal()
                goal.request = req
                goal.planning_options.plan_only = False
                goal.planning_options.replan = True
                goal.planning_options.replan_attempts = 3

                future = self._action_client.send_goal_async(goal)
                rclpy.spin_until_future_complete(self, future, timeout_sec=15.0)

                if not future.done():
                    raise RuntimeError("Goal send timed out — driver likely dropped")

                goal_handle = future.result()
                if not goal_handle.accepted:
                    raise RuntimeError("Goal rejected — controller not running")

                result_future = goal_handle.get_result_async()
                rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0)

                if not result_future.done():
                    raise RuntimeError("Result timed out")

                result = result_future.result().result
                ec = result.error_code.val
                if ec != 1:
                    raise RuntimeError(f"Motion failed — error code: {ec}")

                return True

            except Exception as e:
                self.get_logger().error(f"  Move failed: {e}")
                if attempt < MAX_RETRIES:
                    self.get_logger().warn(
                        f"  Waiting {RETRY_WAIT_S}s for driver to restart before retry..."
                    )
                    time.sleep(RETRY_WAIT_S)
                    self._action_client = ActionClient(self, MoveGroup, "/move_action")
                    self.get_logger().info("  Waiting for MoveGroup action server...")
                    self._action_client.wait_for_server(timeout_sec=30.0)
                    self.get_logger().info("  Reconnected — retrying move...")
                else:
                    self.get_logger().error("  Max retries reached — giving up on this move")
                    return False

        return False

    def go_home(self):
        self.get_logger().info("Moving to home...")
        return self.move_to_mm(HOME_MM, speed_scale=0.3)


# ── Camera setup (matching detect_towers.py) ──────────────────
pipeline = rs.pipeline()
cfg = rs.config()
cfg.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
cfg.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16,  30)
profile = pipeline.start(cfg)

intr  = (profile.get_stream(rs.stream.color)
         .as_video_stream_profile().get_intrinsics())
align = rs.align(rs.stream.color)

# Flush 30 frames on startup — same as detect_towers.py
print("[INFO] Flushing camera pipeline...")
for _ in range(30):
    pipeline.wait_for_frames()
print("[OK]  D405 streaming at 1280x720")

# ── YOLO ──────────────────────────────────────────────────────
print(f"[INFO] Loading model: {WEIGHTS}")
model = YOLO(WEIGHTS)
print(f"[OK]  Model loaded. Classes: {list(model.names.values())}")


# ── Vision helpers ────────────────────────────────────────────
def get_depth_at_pixel(depth_frame, cx, cy, window=5):
    depths = []
    for dx in range(-window, window + 1):
        for dy in range(-window, window + 1):
            px, py = cx + dx, cy + dy
            if 0 <= px < 1280 and 0 <= py < 720:
                d = depth_frame.get_distance(px, py)
                if d > 0:
                    depths.append(d)
    return float(np.median(depths)) if depths else 0


def draw_detections(frame, results):
    """Draw detections using same style as detect_towers.py."""
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
                cv2.line(frame, (cx_box - 20, cy_box), (cx_box + 20, cy_box), colour, 2)
                cv2.line(frame, (cx_box, cy_box - 20), (cx_box, cy_box + 20), colour, 2)
                cv2.circle(frame, (cx_box, cy_box), 5, colour, -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 1)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)

            label = f"{cls_name} {conf:.2f}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - lh - 8), (x1 + lw, y1), colour, -1)
            cv2.putText(frame, label, (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            detections.append({
                "class":  cls_name,
                "conf":   conf,
                "bbox":   (x1, y1, x2, y2),
                "centre": (cx_box, cy_box),
            })
    return frame, detections


def show_live_feed():
    """Live feed with same drawing style as detect_towers.py. SPACE to continue."""
    print("  Live feed — press SPACE when ready to detect")
    while True:
        frames      = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        img     = np.asanyarray(color_frame.get_data())
        results = model(img, verbose=False)
        annotated, _ = draw_detections(img.copy(), results)
        cv2.putText(annotated, "SPACE = detect and continue",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("YOLOv11 Tower Detection", annotated)
        if cv2.waitKey(1) & 0xFF == ord(' '):
            cv2.destroyAllWindows()
            return


def detect_towers(n_frames=10):
    """
    Collect n_frames of detections and return median pose per tower.
    Uses same confidence threshold and class filtering as detect_towers.py.
    """
    for _ in range(5):
        pipeline.wait_for_frames()

    detections = {k: [] for k in TOWERS}
    valid = 0

    for _ in range(n_frames):
        frames      = pipeline.wait_for_frames()
        frames      = align.process(frames)
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            continue

        img     = np.asanyarray(color_frame.get_data())
        results = model(img, verbose=False)
        frame_valid = False

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < CONFIDENCE_THRESHOLD:
                    continue
                cls_name = result.names[int(box.cls[0])]
                if cls_name not in TOWERS:
                    continue
                cx = int((box.xyxy[0][0] + box.xyxy[0][2]) / 2)
                cy = int((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                z  = get_depth_at_pixel(depth_frame, cx, cy)
                if z == 0:
                    continue
                x = (cx - intr.ppx) * z / intr.fx
                y = (cy - intr.ppy) * z / intr.fy
                detections[cls_name].append([x, y, z])
                frame_valid = True

        if frame_valid:
            valid += 1

    if valid < 7:
        print(f"  WARNING: only {valid}/10 valid frames — trial will be flagged")

    result = {}
    for cls_name, pts in detections.items():
        if len(pts) >= 7:
            result[cls_name] = np.median(pts, axis=0)
            print(f"    {cls_name}: x={result[cls_name][0]:.4f} "
                  f"y={result[cls_name][1]:.4f} z={result[cls_name][2]:.4f} m")
        else:
            if pts:
                print(f"    WARNING: {cls_name} only {len(pts)} valid detections — skipped")
    return result, valid


def camera_to_base(pt_cam, tcp_z_mm):
    base_x = PART_ORIGIN[0] + pt_cam[0] * 1000
    base_y = PART_ORIGIN[1] + (-pt_cam[1]) * 1000
    camera_z_mm = tcp_z_mm - CAM_Z_OFFSET
    base_z = camera_z_mm - pt_cam[2] * 1000 + EXT_LENGTH
    return np.array([base_x, base_y, base_z])


# ── Main ──────────────────────────────────────────────────────
def main():
    rclpy.init()
    robot = MoveItController()

    print("\n" + "="*50)
    print(f"  EXPERIMENT — Platform: {PLATFORM}")
    print(f"  Trials: {N_TRIALS}")
    print(f"  Log: {LOG_FILE}")
    print("="*50)

    print("\nMoving to home position...")
    robot.go_home()

    for trial in range(1, N_TRIALS + 1):
        print(f"\n{'='*50}")
        print(f"  TRIAL {trial}/{N_TRIALS}")
        print(f"{'='*50}")

        print("  Moving to observation position...")
        robot.move_to_mm([OBS_X, OBS_Y, OBS_Z_MM], speed_scale=0.3)
        time.sleep(1.0)

        tcp_z_mm = robot.get_tcp_z()

        show_live_feed()

        print("  Detecting towers...")
        tower_positions, valid_frames = detect_towers(n_frames=10)

        if not tower_positions:
            print("  No towers detected — flagging trial and continuing")
            robot.go_home()
            continue

        tower_name = list(tower_positions.keys())[0]
        pt_cam     = tower_positions[tower_name]
        pt_base_mm = camera_to_base(pt_cam, tcp_z_mm)

        if np.any(np.isnan(pt_base_mm)):
            print("  WARNING: NaN in detected position — skipping trial")
            robot.go_home()
            continue

        known_pos = TOWER_KNOWN_POS[tower_name]
        dx = pt_base_mm[0] - known_pos[0]
        dy = pt_base_mm[1] - known_pos[1]
        dz = pt_base_mm[2] - known_pos[2]

        cmd_x = np.array([KNOWN_PROBE_X[0] + dx, KNOWN_PROBE_X[1], KNOWN_PROBE_X[2]])
        cmd_y = np.array([KNOWN_PROBE_Y[0], KNOWN_PROBE_Y[1] + dy, KNOWN_PROBE_Y[2]])
        cmd_z = np.array([KNOWN_PROBE_Z[0], KNOWN_PROBE_Z[1], KNOWN_PROBE_Z[2] + dz])

        print(f"\n  Tower {tower_name} | det: "
              f"X={pt_base_mm[0]:.2f} Y={pt_base_mm[1]:.2f} Z={pt_base_mm[2]:.2f} mm")
        print(f"  Deviation: dX={dx:.2f} dY={dy:.2f} dZ={dz:.2f} mm")

        # ── X axis ────────────────────────────────────────────
        print("\n  → Approach XY")
        robot.move_to_mm(APPROACH_XY_MM, speed_scale=0.1)
        print("  → Probe X zero")
        robot.move_to_mm(PROBE_X_MM, speed_scale=0.1)
        print("  → Offset X")
        robot.move_to_mm([cmd_x[0], cmd_x[1], cmd_x[2]], speed_scale=0.1)
        time.sleep(2.0)
        x_reading = float(input("  X dial gauge reading (mm): "))
        log_result(trial, tower_name, "X", x_reading, pt_base_mm, cmd_x)
        print("  → Back to approach XY")
        robot.move_to_mm(APPROACH_XY_MM, speed_scale=0.1)

        # ── Y axis ────────────────────────────────────────────
        print("\n  → Approach XY")
        robot.move_to_mm(APPROACH_XY_MM, speed_scale=0.1)
        print("  → Probe Y zero")
        robot.move_to_mm(PROBE_Y_MM, speed_scale=0.1)
        print("  → Offset Y")
        robot.move_to_mm([cmd_y[0], cmd_y[1], cmd_y[2]], speed_scale=0.1)
        time.sleep(2.0)
        y_reading = float(input("  Y dial gauge reading (mm): "))
        log_result(trial, tower_name, "Y", y_reading, pt_base_mm, cmd_y)
        print("  → Back to approach XY")
        robot.move_to_mm(APPROACH_XY_MM, speed_scale=0.1)

        # ── Z axis ────────────────────────────────────────────
        print("\n  → Safe Z")
        robot.move_to_mm(SAFE_Z_MM, speed_scale=0.1)
        print("  → Approach Z")
        robot.move_to_mm(APPROACH_Z_MM, speed_scale=0.1)
        print("  → Probe Z zero")
        robot.move_to_mm(PROBE_Z_MM, speed_scale=0.1)
        print("  → Offset Z")
        robot.move_to_mm([cmd_z[0], cmd_z[1], cmd_z[2]], speed_scale=0.1)
        time.sleep(2.0)
        z_reading = float(input("  Z dial gauge reading (mm): "))
        log_result(trial, tower_name, "Z", z_reading, pt_base_mm, cmd_z)
        print("  → Back to approach Z")
        robot.move_to_mm(APPROACH_Z_MM, speed_scale=0.1)
        print("  → Back to safe Z")
        robot.move_to_mm(SAFE_Z_MM, speed_scale=0.1)

        print(f"\n  Trial {trial} complete — returning home")
        robot.go_home()

    pipeline.stop()
    rclpy.shutdown()
    print(f"\nExperiment complete. Results saved to {LOG_FILE}")


if __name__ == "__main__":
    main()