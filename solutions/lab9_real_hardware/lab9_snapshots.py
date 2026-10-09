#!/usr/bin/env python3
"""Lab 9: passive camera snapshots for the report / slides. Subscribes to camera/image and saves one JPEG every <period>
seconds into <out_dir> (file name HHMMSS.jpg). Publishes nothing, never moves the robot.

    source ~/rosenv9.sh
    python3 solutions/lab9_real_hardware/lab9_snapshots.py lab9/eval/runs/<run>/snapshots 2.0     # Ctrl+C to stop
Use it next to "record_run.sh bag <name>" (same run folder); lab9_analyse_run.py --plot uses the snapshots.
"""
import os, sys, time, cv2, rclpy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
out, period = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
os.makedirs(out, exist_ok=True)
rclpy.init(); n = rclpy.create_node("lab9_snapshot_recorder"); b = CvBridge(); last = [0.0]
def cb(msg):
    now = time.time()
    if now - last[0] >= period:
        last[0] = now
        cv2.imwrite(os.path.join(out, time.strftime("%H%M%S", time.localtime(now)) + ".jpg"), b.imgmsg_to_cv2(msg, "bgr8"),
                    [cv2.IMWRITE_JPEG_QUALITY, 85])
n.create_subscription(Image, "camera/image", cb, 1)
try:
    rclpy.spin(n)
except KeyboardInterrupt:
    pass
