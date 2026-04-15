import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import message_filters
from ultralytics import YOLO
from collections import deque
import cv2
import numpy as np
from image_geometry import PinholeCameraModel

class TowerDetector(Node):
    def __init__(self):
        super().__init__('tower_detector')

        # Declare parameters with default values
        self.declare_parameter('show_gui', False)
        
        # Adjust this to slow down the logs
        self.process_every_n_frames = 2
        self.frame_count = 0

        # Create a buffer for pose data
        self.buffer_size = 10  # Number of frames to average
        self.pose_buffers = {cls: deque(maxlen=self.buffer_size) for cls in ["12", "17", "22", "27", "Center"]}

        self.bridge = CvBridge()
        
        # Load your specific model
        self.model = YOLO("/root/ws_moveit/best.pt") 
        self.camera_model = PinholeCameraModel()

        # Colours from your original script
        self.CLASS_COLOURS = {
            "12":     (0,   255, 0),    # green
            "17":     (0,   165, 255),  # orange
            "22":     (255, 0,   0),    # blue
            "27":     (0,   0,   255),  # red
            "Center": (0,   255, 255),  # yellow
        }

        # Subscriptions
        # We need CameraInfo to understand the lens focal length/intrinsics
        self.info_sub = self.create_subscription(
            CameraInfo, '/camera/camera/color/camera_info', self.info_callback, 10)
        
        # Synchronized Subscriptions for Color and Aligned Depth
        self.color_sub = message_filters.Subscriber(self, Image, '/camera/camera/color/image_rect_raw')
        self.depth_sub = message_filters.Subscriber(self, Image, '/camera/camera/aligned_depth_to_color/image_raw')
        
        # ApproximateTimeSynchronizer ensures we process matching frames
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.color_sub, self.depth_sub], queue_size=10, slop=0.1)
        self.ts.registerCallback(self.image_callback)

        self.get_logger().info("Tower Detector Node Initialized")

    def info_callback(self, msg):
        self.camera_model.from_camera_info(msg)

    def image_callback(self, color_msg, depth_msg):
        self.frame_count += 1
        if self.frame_count % self.process_every_n_frames != 0:
            return

        if self.camera_model.projection_matrix() is None:
            return

        show_gui = self.get_parameter('show_gui').get_parameter_value().bool_value

        cv_color = self.bridge.imgmsg_to_cv2(color_msg, "bgr8")
        cv_depth = self.bridge.imgmsg_to_cv2(depth_msg, "passthrough")

        results = self.model(cv_color, verbose=False)
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = r.names[cls_id]
                u, v = int(box.xywh[0][0]), int(box.xywh[0][1])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                z_mm = cv_depth[v, u]
                if z_mm > 0:
                    z_m = z_mm / 1000.0
                    ray = self.camera_model.project_pixel_to_3d_ray((u, v))
                    raw_point = np.array([ray[0] * z_m, ray[1] * z_m, z_m])
                    
                    # 1. Update the Buffer
                    if cls_name in self.pose_buffers:
                        self.pose_buffers[cls_name].append(raw_point)
                        
                        # 2. Calculate Average if buffer is ready
                        if len(self.pose_buffers[cls_name]) >= self.buffer_size:
                            avg_point = np.mean(self.pose_buffers[cls_name], axis=0)
                            
                            # Log the stable data
                            self.get_logger().info(f"STABLE {cls_name} -> X:{avg_point[0]:.3f} Y:{avg_point[1]:.3f} Z:{avg_point[2]:.3f}")

                            # 3. Drawing Logic (Only if GUI is requested)
                            if show_gui:
                                color = self.CLASS_COLOURS.get(cls_name, (255, 255, 255))
                                cv2.rectangle(cv_color, (x1, y1), (x2, y2), color, 2)
                                
                                # Use the AVERAGED Z for the label text
                                label = f"{cls_name} AVG Z: {avg_point[2]:.3f}m"
                                cv2.putText(cv_color, label, (x1, y1 - 10), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Final check to show window
        if show_gui:
            cv2.imshow("YOLOv11 ROS 2 Detector", cv_color)
            cv2.waitKey(1)
        else:
            cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = TowerDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()