import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2

def test_cv_bridge():
    print(f"Using Numpy version: {np.__version__}")
    bridge = CvBridge()
    
    # 1. Create a fake ROS Image message
    msg = Image()
    msg.height = 480
    msg.width = 640
    msg.encoding = 'rgb8'
    msg.step = 640 * 3
    msg.data = np.zeros((480, 640, 3), dtype=np.uint8).tobytes()

    try:
        # 2. Try to convert ROS -> OpenCV (This is where NumPy conflicts happen)
        cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        print("✅ Conversion ROS -> OpenCV successful!")
        
        # 3. Try to convert OpenCV -> ROS
        ros_msg = bridge.cv2_to_imgmsg(cv_img, encoding='bgr8')
        print("✅ Conversion OpenCV -> ROS successful!")
        
    except Exception as e:
        print(f"❌ Bridge Error: {e}")

if __name__ == '__main__':
    test_cv_bridge()