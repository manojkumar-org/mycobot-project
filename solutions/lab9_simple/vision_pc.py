#!/usr/bin/env python3
"""Lab 9 simple, Lab PC side: camera + YOLO -> cube colour and top-centre position in the robot frame -> Pi.

Mapping image -> robot: the 2 ArUco marker centres (measured in the robot frame) give a 2D similarity
(scale, rotation, shift); the camera looks straight down, so that is enough for the plate plane.
Cube tops are CUBE_MM (35 mm) above the plate, so their pixel is shifted outwards; top_to_xy() undoes that (parallax).

Run (README step 4): ~/venvs/mycobot/bin/python vision_pc.py   (ROS sourced, ROS_DOMAIN_ID=47)
Keys in the window: space = ARMED/SAFE, c = re-read markers, s = save frame, q = quit.
WARNING: ARMED means every stable cube on the plate is sent to the robot. Start SAFE, check the overlay first.
"""
import math
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C  # noqa: E402

FRAMES_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "lab9", "frames"))


# ---------------- markers ----------------
def detect_markers(img):
    """{id: 4x2 corner array} for all markers of C.ARUCO_DICT (OpenCV >= 4.7 and older API)."""
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, C.ARUCO_DICT))
    if hasattr(cv2.aruco, "ArucoDetector"):
        corners, ids, _ = cv2.aruco.ArucoDetector(d, cv2.aruco.DetectorParameters()).detectMarkers(img)
    else:
        corners, ids, _ = cv2.aruco.detectMarkers(img, d, parameters=cv2.aruco.DetectorParameters_create())
    return {} if ids is None else {int(i): c[0] for i, c in zip(ids.ravel(), corners)}


class PlaneMap:
    """Pixel (u, v) <-> robot (x, y) mm on the plate.  w = a*z + b with z = u - i*v, w = x + i*y.
    v is flipped because image y points down; seen from above, (u, -v) and (x, y) are both right-handed."""

    def __init__(self, px, mm, frame_wh):
        i1, i2 = sorted(mm)
        z1, z2 = (complex(px[i][0], -px[i][1]) for i in (i1, i2))
        w1, w2 = (complex(*mm[i]) for i in (i1, i2))
        self.a = (w2 - w1) / (z2 - z1)
        self.b = w1 - self.a * z1
        self.px = px
        # plate point straight under the camera ~ image centre (camera looks down)
        self.cam_xy = self.to_robot(frame_wh[0] / 2, frame_wh[1] / 2)

    def to_robot(self, u, v):
        w = self.a * complex(u, -v) + self.b
        return w.real, w.imag

    def to_image(self, x, y):
        z = (complex(x, y) - self.b) / self.a
        return z.real, -z.imag

    def top_to_xy(self, u, v, h):
        """Robot xy of a point h mm above the plate seen at pixel (u, v)."""
        x, y = self.to_robot(u, v)                      # where the ray meets the plate
        cx, cy = self.cam_xy
        k = (C.CAMERA_HEIGHT_MM - h) / C.CAMERA_HEIGHT_MM
        return cx + (x - cx) * k, cy + (y - cy) * k

    def report(self, side_px):
        lines = [f"scale {abs(self.a):.3f} mm/px, rotation {math.degrees(np.angle(self.a)):.1f} deg, "
                 f"camera over ({self.cam_xy[0]:.0f}, {self.cam_xy[1]:.0f}) mm"]
        if C.MARKER_SIDE_MM:
            est = side_px * abs(self.a)
            err = 100 * (est / C.MARKER_SIDE_MM - 1)
            lines.append(f"marker side: {est:.1f} mm from map vs {C.MARKER_SIDE_MM} measured ({err:+.0f} %)"
                         + ("  <-- CHECK MARKERS_MM" if abs(err) > 10 else ""))
        return lines


def calibrate(frames):
    """Median marker centres over several frames -> PlaneMap, or None if a marker is missing."""
    seen = {i: [] for i in C.MARKERS_MM}
    sides = []
    for f in frames:
        for i, c in detect_markers(f).items():
            if i in seen:
                seen[i].append(c.mean(0))
                sides.append(np.linalg.norm(c - np.roll(c, 1, 0), axis=1).mean())
    missing = [i for i, v in seen.items() if not v]
    if missing:
        print(f"[calib] marker(s) {missing} not visible ({C.ARUCO_DICT}); clear them and press c")
        return None
    px = {i: tuple(np.median(v, 0)) for i, v in seen.items()}
    pm = PlaneMap(px, C.MARKERS_MM, frames[0].shape[1::-1])
    for line in pm.report(float(np.median(sides))):
        print("[calib]", line)
    if not C.MARKERS_MEASURED:
        print("[calib] MARKERS_MM are a GUESS (config.MARKERS_MEASURED = False): sending is locked")
    return pm


# ---------------- drawing ----------------
def P(pt):
    return tuple(int(round(c)) for c in pt)


def draw_map(img, pm):
    ws = [(C.WS_X[0], C.WS_Y[0]), (C.WS_X[1], C.WS_Y[0]), (C.WS_X[1], C.WS_Y[1]), (C.WS_X[0], C.WS_Y[1])]
    cv2.polylines(img, [np.array([P(pm.to_image(*p)) for p in ws])], True, (0, 255, 255), 1)
    o = pm.to_image(0, 0)
    cv2.circle(img, P(o), 6, (255, 0, 255), 2)
    cv2.arrowedLine(img, P(o), P(pm.to_image(50, 0)), (0, 0, 255), 2)   # +x 50 mm red
    cv2.arrowedLine(img, P(o), P(pm.to_image(0, 50)), (0, 255, 0), 2)   # +y 50 mm green
    cv2.putText(img, "base", P((o[0] + 8, o[1] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1)
    for i, (u, v) in pm.px.items():
        cv2.drawMarker(img, P((u, v)), (255, 0, 0), cv2.MARKER_CROSS, 14, 2)
        cv2.putText(img, f"id{i}", P((u + 8, v - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
    for col, (x, y) in C.BIN_COORDS.items():
        u, v = pm.to_image(x, y)
        if 0 <= u < img.shape[1] and 0 <= v < img.shape[0]:
            cv2.circle(img, P((u, v)), 10, (255, 255, 255), 1)
            cv2.putText(img, f"bin {col}", P((u - 20, v + 24)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)


# ---------------- detection ----------------
def detect_cubes(model, frame, pm):
    """List of dicts: color, u, v, x, y (mm), yaw (deg, -45..45), inside (workspace)."""
    r = model(frame, conf=C.YOLO_CONF, verbose=False)[0]
    out = []
    if r.boxes is None or len(r.boxes) == 0:
        return out
    boxes = r.boxes.xyxy.cpu().numpy()
    cls = r.boxes.cls.cpu().numpy().astype(int)
    conf = r.boxes.conf.cpu().numpy()
    kps = r.keypoints.xy.cpu().numpy() if r.keypoints is not None else None
    for i in range(len(boxes)):
        side_mm = max(boxes[i][2] - boxes[i][0], boxes[i][3] - boxes[i][1]) * abs(pm.a)
        if not C.BOX_MM[0] <= side_mm <= C.BOX_MM[1]:
            continue                                      # not cube-sized (e.g. the white plate)
        color = C.CLASS_TO_COLOR.get(model.names[cls[i]], model.names[cls[i]])
        if kps is not None and kps[i][4].any():           # keypoint 4 = top-face centre (course model)
            u, v = kps[i][4]
            h = C.CUBE_MM
        else:                                             # fallback: box centre ~ half height
            u, v = (boxes[i][:2] + boxes[i][2:]) / 2
            h = C.CUBE_MM / 2
        x, y = pm.top_to_xy(u, v, h)
        yaw = float("nan")
        if kps is not None and kps[i][0].any() and kps[i][1].any():   # keypoints 0 -> 1 = one top edge
            (x0, y0), (x1, y1) = pm.to_robot(*kps[i][0]), pm.to_robot(*kps[i][1])
            yaw = (math.degrees(math.atan2(y1 - y0, x1 - x0)) + 45) % 90 - 45
        inside = C.WS_X[0] <= x <= C.WS_X[1] and C.WS_Y[0] <= y <= C.WS_Y[1]
        out.append(dict(color=color, conf=float(conf[i]), box=boxes[i], u=u, v=v, x=x, y=y, yaw=yaw,
                        inside=inside, kps=None if kps is None else kps[i]))
    return out


def draw_cubes(img, dets, target):
    for d in dets:
        col = (0, 255, 0) if d["inside"] else (0, 0, 255)
        x1, y1, x2, y2 = d["box"].astype(int)
        cv2.rectangle(img, (x1, y1), (x2, y2), col, 2 if d is target else 1)
        if d["kps"] is not None:
            for k in d["kps"]:
                if k.any():
                    cv2.circle(img, P(k), 3, (255, 0, 0), -1)
        cv2.putText(img, f"{d['color']} {d['conf']:.2f}", (x1, y1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
        cv2.putText(img, f"x{d['x']:.0f} y{d['y']:.0f} yaw{d['yaw']:.0f}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)


def pick_target(dets):
    ok = [d for d in dets if d["inside"] and d["color"] in C.COLOR_ORDER]
    return min(ok, key=lambda d: C.COLOR_ORDER.index(d["color"])) if ok else None


# ---------------- ROS ----------------
class Sender:
    def __init__(self):
        try:
            import rclpy
            from geometry_msgs.msg import PointStamped
        except ImportError as e:
            sys.exit(f"[ros] {e}: run `source /opt/ros/jazzy/setup.bash` in this terminal first")
        if os.environ.get("ROS_DOMAIN_ID") != "47":
            print(f"[ros] WARNING: ROS_DOMAIN_ID={os.environ.get('ROS_DOMAIN_ID')} (Pi uses 47) -> the Pi will not see targets")
        rclpy.init()
        self.node = rclpy.create_node("simple_pp_vision")
        self.pub = self.node.create_publisher(PointStamped, C.TOPIC, 1)
        self.Msg = PointStamped
        print(f"[ros] publishing on {C.TOPIC}")

    def send(self, d):
        m = self.Msg()
        m.header.stamp = self.node.get_clock().now().to_msg()
        m.header.frame_id = d["color"]
        m.point.x, m.point.y = d["x"] / 1000.0, d["y"] / 1000.0
        m.point.z = (C.SURFACE_Z_MM + C.CUBE_MM) / 1000.0
        self.pub.publish(m)
        return True

    def close(self):
        import rclpy
        self.node.destroy_node()
        rclpy.shutdown()


# ---------------- main ----------------
def open_camera():
    cap = cv2.VideoCapture(C.CAMERA_DEVICE, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, C.FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, C.FRAME_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)     # newest frame, YOLO on CPU is slower than 30 fps
    if not cap.isOpened():
        sys.exit(f"camera {C.CAMERA_DEVICE} not available")
    ok, f = cap.read()
    if not ok:
        sys.exit("camera gives no frames")
    print(f"[cam] {f.shape[1]}x{f.shape[0]}")
    return cap


def grab(cap, n):
    frames = []
    while len(frames) < n:
        ok, f = cap.read()
        if ok:
            frames.append(f)
    return frames


def save(img, tag):
    os.makedirs(FRAMES_DIR, exist_ok=True)
    path = os.path.join(FRAMES_DIR, f"simple_{tag}_{time.strftime('%Y%m%d_%H%M%S')}.png")
    cv2.imwrite(path, img)
    print("[save]", path)


def main():
    if not os.path.exists(os.path.expanduser(C.YOLO_WEIGHTS)):
        sys.exit(f"weights missing: {C.YOLO_WEIGHTS} (copy best.pt from Lab 09 PP.zip)")
    from ultralytics import YOLO
    model = YOLO(os.path.expanduser(C.YOLO_WEIGHTS))
    print("[yolo] classes:", model.names)
    if not C.MARKERS_MEASURED:
        print("[WARNING] config.MARKERS_MEASURED = False: marker positions are a guess, sending is LOCKED (README step 3)")
    print("[WARNING] keep the markers uncovered at start; check the overlay before pressing space")

    cap = open_camera()
    pm = calibrate(grab(cap, 20))
    sender = Sender()
    armed, cand, t0, last_send = False, None, 0.0, 0.0
    cv2.namedWindow("lab9 simple", cv2.WINDOW_NORMAL)
    try:
        while True:
            frame = grab(cap, 1)[0]
            vis = frame.copy()
            target = None
            if pm is not None:
                draw_map(vis, pm)
                dets = detect_cubes(model, frame, pm)
                target = pick_target(dets)
                draw_cubes(vis, dets, target)
            now = time.time()
            # stability: same colour, within STABLE_MM, for STABLE_S
            if target is None:
                cand = None
            elif cand is None or cand["color"] != target["color"] or \
                    math.hypot(cand["x"] - target["x"], cand["y"] - target["y"]) > C.STABLE_MM:
                cand, t0 = target, now
            stable = cand is not None and now - t0 >= C.STABLE_S
            if armed and stable and now - last_send >= C.RESEND_S:
                sender.send(target)
                last_send = now
                print(f"[send] {target['color']} x {target['x']:.1f} y {target['y']:.1f} mm")
            status = ("ARMED" if armed else "SAFE") + (" | stable" if stable else "") + \
                     ("" if pm else " | NO CALIB (c)") + " | space=arm c=calib s=save q=quit"
            cv2.putText(vis, status, (8, vis.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 0, 255) if armed else (0, 255, 255), 1)
            cv2.imshow("lab9 simple", vis)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                break
            if k == ord("s"):
                save(frame, "raw")
                save(vis, "overlay")
            if k == ord("c"):
                pm = calibrate(grab(cap, 20)) or pm
            if k == ord(" "):
                if not C.MARKERS_MEASURED:
                    print("[arm] locked: measure MARKERS_MM and set MARKERS_MEASURED = True")
                elif pm is None:
                    print("[arm] locked: no calibration")
                else:
                    armed = not armed
                    print("[arm]", "ARMED: stable cubes are sent to the robot" if armed else "SAFE: nothing is sent")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        sender.close()


if __name__ == "__main__":
    main()
