# CoRobot Lab: project map + game plan

Reference for the group (on the lab laptop and on the robot's Raspberry Pi).
Replaces the old `GAME-PLAN.md` (merged here 2026-09-28). Last updated **2026-09-30**.

Course: CoRobot Lab, TU Dortmund, **Mon 28.09.2026**, Mo–Fr 9:00–17:00, IRF Mobile Robot Lab Area.
Moodle: https://moodle.tu-dortmund.de/course/view.php?id=59336 · TAs: Shreyas Desikan, Kavish Punitbhai Gajjar

---

## 1. The course in one paragraph

Groups of 2–3, 9 labs on the **myCobot 280 Pi** (6-DOF, Raspberry Pi 4 inside, suction pump, top camera).
You upload solution code; **the grade comes from a final interview** where you explain your code, the robot
behaviour and the theory. LLMs are allowed for help, but you must understand everything you submit, and you
can't use them in the interview. So: **understanding > finishing.**

| # | Lab (PDF) | Tasks | Notebook | Runs on | What it's really about |
|---|---|---|---|---|---|
| 1 | Spatial Transformations | 33 | SpatialTransformations | laptop | rotations, homogeneous T, RPY/Euler/axis-angle, quaternions, SLERP |
| 2 | Forward Kinematics | 29 | ForwardKinematics | laptop + RViz2 | DH table, manual vs URDF model, publish joints to ROS |
| 3 | Inverse Kinematics | 18 | InverseKinematics | laptop (last task robot) | numerical IK: rtb solver, `least_squares`, damped least squares, seeds |
| 4 | Differential Kinematics | 20 | DifferentialKinematics | laptop (last 2 robot) | Jacobian, singularities (SVD), manipulability, resolved-rate control |
| 5 | TCP Calibration | 18 | TCPCalibration | robot measurements | flange→TCP offset, SVD mean rotation, residuals |
| 6 | Trajectory Planning | 19 | TrajectoryPlanning | laptop | trapezoid/triangle profiles, synchronised joints. **Moodle quiz before the lab** |
| 7 | Serial Communication | 29 | SerialCommunicationRobotControl | **Pi** | frames `FE FE LEN CMD … FA`, read/send angles, stop/resume, position vs velocity mode |
| 8 | Pick & Place v1 (`Pick_And_Place.pdf`, Apr) | 28 | PickAndPlace | **Pi** | YOLO + solvePnP + pymycobot + GPIO pump |
| 9 | Pick & Place v2 (`Pick_And_Place-2.pdf`, Sep 23) | explore + **2 of 5** extensions | none | **Pi** + MoveIt | Brain/Vision/MoveIt/Controller nodes, HSV, ArUco |

Every notebook starts with `%matplotlib widget` → **`ipympl` must be installed** in the venv.
Labs 2–6 load `mycobot_280_gazebo.urdf` from the repo root; Labs 3–5 also import `helperFunctions.py`.

---

## 2. Where things run

| Machine | What runs there | Why |
|---|---|---|
| **Lab laptop** (Ubuntu 24.04, ROS 2 Jazzy, `~/venvs/mycobot`) | Labs 1–6 notebooks, RViz2 | no robot needed |
| **Robot Pi** `ssh cobot` (= `cobot@129.217.130.85`) | Labs 7–9: serial, `mycobot_control`, Jupyter kernel, pick & place | robot is wired to the Pi's UART `/dev/ttyAMA0` (= `serial0`); the laptop has **no** serial/USB link to the robot |

**Work from the laptop and keep the Pi light.** VS Code Remote-SSH to the Pi is fine, but with **no extensions
installed on the Pi** (`~/.vscode-server/extensions` empty). On 2026-09-28 remote extensions (Pylance ~730 MB,
Copilot) used up the Pi's 1.8 GB and hung it (SSH banner timeouts). Reach the Pi through SSH (§6c).
Claude Code runs on the laptop and uses `ssh cobot` for read-only checks only; **[Pi]** steps (sudo, tokens,
passwords, robot motion) are run by a person (§9 rule 8). Architecture diagram: README.md → "How it runs".

Pi facts (checked 2026-09-30): hostname `cobot-pi1` · Raspberry Pi 4 Model B Rev 1.4 · **Ubuntu 24.04.5 LTS** ·
**ROS 2 Jazzy** · **RAM 1.8 GB, no swap** (budget: ROS + Jupyter only; ~1.5 GB available at idle) · arm64 ·
Python 3.12 · venv `~/venvs/mycobot` · internet OK (git pull from GitHub works).

Serial (checked 2026-09-30): the robot UART is **`/dev/ttyAMA0`** (PL011 on GPIO 14/15, via `dtoverlay=disable-bt`;
device-tree alias `serial0` → `serial@7e201000` = `ttyAMA0`). Ubuntu has **no udev rule** for the `/dev/serial0` link
that Raspberry Pi OS creates, so `/dev/serial0` doesn't exist until `/etc/udev/rules.d/99-serial0.rules` is added
(README setup step 2). The course code for Labs 7–9 opens `/dev/serial0`. Lab 7 task 7 read six angles through
`ttyAMA0`. (Earlier notes claiming `/dev/serial0` worked on 2026-09-28 were never verified.)
Still `TODO`: group `ROS_DOMAIN_ID` (ask TAs).

**Software on the Pi per lab** (checked 2026-09-30; system `/usr/bin/python3` with ROS Jazzy sourced):

| Lab | Pi part | Pi has | Pi lacks |
|---|---|---|---|
| 7 | whole lab | `serial`, numpy, matplotlib, `rclpy`/`sensor_msgs`/`std_msgs` (with ROS sourced) | nothing (`ipympl` only in the venv; system kernel → `%matplotlib inline`) |
| 2 | tasks 18–29 (controller + publish `/mycobot/joint_command`) | `rclpy`, msgs | `roboticstoolbox`, `spatialmath` (tasks 1–17), RViz2 is a GUI → laptop |
| 8 | `motion_node` (pymycobot + pump GPIO), GPIO notebook cells | `pymycobot` 4.0.7 (`~/.local`) | `RPi.GPIO`, `cv2`, `ultralytics`/`torch` (YOLO) |
| 9 | `mycobot_controller` (pymycobot + pump GPIO) | `pymycobot` | `RPi.GPIO`, `control_msgs`, **MoveIt** (none in `/opt/ros/jazzy`), `moveit_msgs`, `cv2`, `cv_bridge` |
| 3–5 | **not run on the Pi** (decision 2026-09-30) | | |

Other facts: **the camera (Logitech C930e) is plugged into the laptop** (`/dev/video0`); the Pi's `/dev/video10–20` are its
built-in codec devices, not a camera. `colcon` on the Pi is the apt one (`/usr/bin/colcon`), so built ROS nodes run on
the system Python, not the venv. arm64 wheels exist for `roboticstoolbox-python`, `spatialmath-python`,
`opencv-python`, `torch`; apt has `python3-rpi.gpio`, `python3-opencv`, `ros-jazzy-cv-bridge`, `ros-jazzy-control-msgs`,
`ros-jazzy-moveit` (none installed). Likely split (unconfirmed, §11 Q6): robot driver + GPIO on the Pi; RViz2,
vision (camera) and MoveIt on the laptop, talking to the Pi over ROS 2.

---

## 3. Repo map

```
~/mycobot-project/                (same path on laptop and Pi)
├── gameplan.md                   this file
├── README.md                     machine setup: GitHub login, clone, venv, build, Jupyter over SSH
├── *Template.ipynb               8 lab notebooks, WORK HERE (see §1)
├── helperFunctions.py            used by IK / Differential / TCP notebooks
├── serial_iface.py               used by Lab 7 (byte-identical copy of ros2_ws/.../mycobot_control/serial_iface.py)
│                                 (+ mycobot_280_gazebo.urdf here once you have it)
├── solutions/                    worked solutions with explanations, one notebook per lab (compare with the templates)
├── ros2_ws/src/                  Labs 2–7  (from FK_to_TP Control.zip): mycobot_control, mycobot_description
├── pp_moveit_ws/src/             Lab 9     (from Pick and Place Packages.zip): brain, vision, controller, interfaces, MoveIt 2 config, 280pi tools, mycobot_description
├── pp_yolo_ws/src/               Lab 8     (from Lab 09 PP.zip): vision (YOLO), mycobot_msgs, mycobot_motion_v1
│   └── Vision_requirements/      Lab 8 pip requirements (numpy 2.x → own venv `yolovenv`)
└── pdfs/                         lab PDFs, private (in .git/info/exclude, never commit)
```

**Why 3 workspaces:** `mycobot_description` and `mycobot_controller` exist in more than one course zip, and
duplicate package names break `colcon build`. The two `mycobot_description` copies are byte-identical (277 MB each on
disk, stored once by git). `Pick and Place Control.zip` was not extracted: its controller is identical to the one in
the Packages zip. Workspace code is unchanged from the zips.

**Not in the repo:** `mycobot_280_gazebo.urdf` (in none of the zips; get it from Moodle/TAs). Until then,
`ros2_ws/src/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf` has the same `g_base` → `joint6_flange`
chain for trying things out, **not** for results you hand in. `best.pt` YOLO weights (40 MB) go to
`pp_yolo_ws/weights/`. Git ignores `build/ install/ log/ *.zip *.pt`.

---

## 4. Workspaces and packages

### ros2_ws (Labs 2–7)
| Package | Contents |
|---|---|
| `mycobot_control` | ROS 2 node `mycobot_control` (serial ↔ ROS bridge, §5), `launch/mycobot_control.launch.py`, `scripts/fk_tool_calib.py`, `scripts/ik_debug.py`. `pi_motion3_node.py` sits at the package root, is **not** an entry point, and belongs to Lab 8 (imports `mycobot_msgs`, `RPi.GPIO`, `pymycobot`). |
| `mycobot_description` | URDFs + meshes for 7 myCobot 280 variants; we use `urdf/mycobot_280_pi/` |

### pp_moveit_ws (Lab 9)
| Package | Entry points / launch | Role |
|---|---|---|
| `mycobot_brain` | `brain`, `brain_test`; `brain.launch.py`, `brain_simulation.launch.py` | task logic: asks vision for cube coords, plans with MoveIt (`/plan_kinematic_path`, `/compute_cartesian_path`), adds collision objects |
| `mycobot_vision` | `vision`, `vision2` | camera + HSV detection, serves `/cube_coordinates` (`GetCubeCoords`) |
| `mycobot_controller` | `controller`, `test` | executes on the robot, pump via `/pump_controller` |
| `mycobot_interfaces` | msgs `MycobotAngles/Coords/SetAngles/SetCoords/GripperStatus/PumpStatus`; srvs `GetAngles/GetCoords/GetCubeCoords/SetAngles/SetCoords/GripperStatus/PumpStatus` | custom interfaces |
| `mycobot_280_moveit2` | `demo`, `move_group`, `moveit_rviz`, `rsp`, … launch files | MoveIt 2 config |
| `mycobot_280pi` | `slider_control`, `simple_gui`, `listen_real`, `teleop_keyboard`, `opencv_camera`, … | Elephant Robotics tools; several hardcode `/dev/ttyAMA0` |

Lab 9 extensions (choose two): ① ArUco camera calibration ② robust HSV masking ③ interactive HSV threshold
calibration ④ shape detection (cube vs cylinder) ⑤ select object by colour + shape.
**Low-risk pair:** ②+③ (pure OpenCV, can be developed at home on saved camera images).
**Best for the interview:** ①+② (① reuses the transform maths from Labs 1–2).

### pp_yolo_ws (Lab 8, ask TAs whether still required)
`vision` (`vision_node`: YOLO pose + solvePnP → `DetectedObject`), `mycobot_msgs` (`DetectedObject`, `JointVelocity`),
`mycobot_motion_v1` (`motion_node`: pymycobot + GPIO pump). Needs its own venv `yolovenv` (numpy 2.x).
Hardcoded in `vision_node.py`: weights `/home/tejas/YOLO/.../best.pt` (ours: `pp_yolo_ws/weights/best.pt`),
`CALIB_FILE /home/tejas/z_scale_calibration.json`, camera `/dev/video2`. Adjust only when you actually run it.

---

## 5. Robot interface (Lab 7 core)

### Serial protocol (`serial_iface.py`, class `MyCobotSerialInterface`)
- Port **`/dev/ttyAMA0`** (course code uses the link `/dev/serial0`, §2), **1 000 000 baud**, timeout 0.05 s.
  Only **one** process may hold the port.
- Frame: `FE FE LEN CMD [payload] FA`, `LEN` = bytes from CMD through FA inclusive.
- Commands: read angles `0x20`, send angles `0x22`, resume `0x28`, stop `0x29`, jog `0x34`.
  - read request `FE FE 02 20 FA` → reply `FE FE 0E 20 <12 bytes> FA` (6 × int16 big-endian, degrees × 100)
  - send `FE FE 0F 22 <6 × int16> <speed 1–100> FA`
  - stop `FE FE 02 29 FA`; after a stop, motion is ignored until resume `FE FE 02 28 FA`
- API: `read_angles_deg()`, `send_angles_deg(angles, speed)`, `stop_motion()`, `resume_motion()`, `close()`.

### ROS 2 node `mycobot_control` (`ros2 launch mycobot_control mycobot_control.launch.py`)
| Topic | Type | Direction | Units |
|---|---|---|---|
| `/mycobot/joint_command` | Float64MultiArray | in | position, **rad** |
| `/mycobot/joint_velocity` | Float64MultiArray | in | **rad/s**; deadband 0.01, max 150 °/s, accel ramp 1 rad/s², all-zero = stop |
| `/mycobot/ee_pose` | Float64MultiArray | in | `[x_mm, y_mm, z_mm, roll_deg, pitch_deg, yaw_deg]`, needs the URDF for IK |
| `/mycobot/joint_states` | JointState | out | rad, 5 Hz |

Launch params worth knowing: `port /dev/serial0` (needs the udev link, §2), `cmd_tick_hz 20`, `state_rate_hz 5`, `max_step_deg 2`,
`allow_uninitialized False` (velocity ignored until a first angle read succeeds), `log_tx True`.
`urdf_path` is hardcoded to `/home/mycobot/ros2_ws/src/mycobot_280_gazebo.urdf`; if that file is missing the node
logs `urdf_path not found` and `/mycobot/ee_pose` IK is unavailable (joint topics still work).
`scripts/ik_debug.py` and `scripts/fk_tool_calib.py` point at `/home/harshit/...` (ik_debug takes `--urdf`).

---

## 6. Environment setup

### 6a. Laptop (done 2026-09-28; keep for reinstalls)
ROS 2 Jazzy via the **official** `ros2-apt-source` .deb (never also the PDF's manual `ros.key`/`ros2.list`: apt
error "Conflicting values set for option Signed-By"); `ros-dev-tools` instead of the PDF's separate dev tools.
```bash
sudo apt update && sudo apt upgrade -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update && sudo apt install ros-jazzy-desktop ros-dev-tools
# ~/.bashrc: one line `source /opt/ros/jazzy/setup.bash` (no duplicates)
sudo rosdep init && rosdep update
ros2 run demo_nodes_cpp talker     # + in a 2nd terminal: ros2 run demo_nodes_py listener
```
Venv notes:
- `--system-site-packages` is required: a plain venv can't see apt's `em`, `lark`, `catkin_pkg`, so building message
  packages (`mycobot_msgs`, `mycobot_interfaces`) fails with `No module named 'em'`. Fix an existing venv with
  `sed -i 's/^include-system-site-packages = false/include-system-site-packages = true/' ~/venvs/mycobot/pyvenv.cfg`.
- Keep pip `colcon-common-extensions` in the venv: nodes built with it run on the venv's Python.
- `numpy<2` keeps ROS's compiled parts (e.g. `cv_bridge`, built against numpy 1.26) working. Lab 8 YOLO uses
  numpy 2.x → own venv `yolovenv`.
- `rosdep -r` continues past keys that can't resolve on a laptop. Expected: `gazebo_ros_control` (Gazebo Classic,
  not in Jazzy), `python3-rpi.gpio` (only on the Pi), `python3-pymycobot` (pip-installed).

Start Jupyter on the laptop:
```bash
source ~/venvs/mycobot/bin/activate
source ~/mycobot-project/ros2_ws/install/setup.bash     # ROS itself is sourced by .bashrc
cd ~/mycobot-project && jupyter lab
```
Smoke test: `import rclpy, roboticstoolbox as rtb, spatialmath; print("ok")`.

### 6b. Robot Pi
Steps are in **README.md → "Robot Pi"** (Start / Stop steps, one-time setup, troubleshooting). Checklist:
- [x] Clone with a fine-grained token (owner `manojkumar-org`, only `mycobot-project`, *Contents: Read and write*, 30 days)
- [x] All VS Code remote extensions removed from the Pi; Remote-SSH works without extensions
- [x] venv `~/venvs/mycobot` + JupyterLab + `ipympl` + `pyserial`; Jupyter reached via SSH tunnel from the laptop
- [x] Serial port works via `/dev/ttyAMA0`: Lab 7 task 7 read six angles
- [x] SSH key + `Host cobot` alias on the laptop (§6c), 2026-09-30; `ssh cobot '…'` works without a password
- [x] Pi repo on `myCobot-lab` at `070cdf2` (2026-09-30)
- [ ] **[Pi]** udev link `/dev/serial0` → `ttyAMA0` (README setup step 2); needed before Lab 7 Part 2 / Labs 8–9
- [ ] **[Pi]** optional: `sudo locale-gen en_US.UTF-8` (silences the `setlocale` warning on every SSH command)
- [ ] Build for Part 2: `colcon build --symlink-install --parallel-workers 1 --packages-select mycobot_description mycobot_control`
- [ ] `~/rosenv.sh` on the Pi (§6c), so non-interactive `ssh cobot '…'` commands see ROS and the venv

Read-only probe (moves nothing), to confirm the port:
```python
import serial, time
s = serial.Serial('/dev/ttyAMA0', 1_000_000, timeout=0.5)
s.reset_input_buffer(); s.write(bytes([0xFE,0xFE,0x02,0x20,0xFA])); s.flush(); time.sleep(0.2)
print(s.read(64).hex(' ')); s.close()     # expect: fe fe 0e 20 ... fa
```

### 6c. Working on the Pi from the laptop (VS Code stays on the laptop)

| Need | How |
|---|---|
| Run a command on the Pi | `ssh cobot '<command>'`; with ROS: `ssh cobot 'source ~/rosenv.sh && ros2 topic list'` |
| Claude Code (on the laptop) | read-only `ssh cobot '…'` checks; **[Pi]** steps (sudo, tokens, motion) are prompted and run by you |
| Read/edit Pi files with normal tools | sshfs mount: Pi `~/mycobot-project` appears at laptop `~/pi-mycobot` |
| Long-running things (controller, Jupyter) | one SSH terminal per process, kept open (Ctrl+C stops it); for "survives closing the window" use `nohup … &` + a log file. `tmux` is optional |
| Notebooks | JupyterLab runs on the Pi (kernel there sees `/dev/ttyAMA0`); laptop connects through an SSH port forward |
| Git for the Pi clone | run git on the Pi: `ssh cobot 'cd ~/mycobot-project && git status'` (git over sshfs is slow) |

Laptop `~/.ssh/config` (installed 2026-09-30, backup `~/.ssh/config.bak-2026-09-30`; one shared connection, reused by
every `ssh cobot` call → measured 0.96 s for the first call, 0.04 s for the next):
```
Host cobot 129.217.130.85
  HostName 129.217.130.85
  User cobot
  IdentityFile ~/.ssh/id_ed25519
  ConnectTimeout 30
  ServerAliveInterval 30
  ServerAliveCountMax 4
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 10m
```
Key (once, done): `ssh-keygen -t ed25519` then `ssh-copy-id cobot`. Scripted `ssh` calls can't type passwords, so the key is required.

Pi `~/rosenv.sh` (non-interactive SSH skips `~/.bashrc`, so ROS must be sourced explicitly):
```bash
source /opt/ros/jazzy/setup.bash
[ -f ~/mycobot-project/ros2_ws/install/setup.bash ] && source ~/mycobot-project/ros2_ws/install/setup.bash
source ~/venvs/mycobot/bin/activate
```

Mount / unmount (laptop): `sshfs cobot:/home/cobot/mycobot-project ~/pi-mycobot -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3`
→ `fusermount -u ~/pi-mycobot`. Avoid broad searches over the mount (the 277 MB `mycobot_description` is slow over the network).

Jupyter: see the bring-up table in README.md (Pi, own terminal: `jupyter lab --no-browser --ip=127.0.0.1 --port 8888`,
laptop `ssh -N -L 8888:localhost:8888 cobot`, browser with the token link).

---

## 7. Lab 7 runbook (Part 1, tasks 1–15: direct serial; controller must NOT run)

| Task | Action |
|---|---|
| 1 | read `serial_iface.py` + `mycobot_control.py` (the PDF asks for this first) |
| 2 | `serial_port='/dev/ttyAMA0'` (or `/dev/serial0` once the link exists), `baud_rate=1_000_000`, `timeout_s=0.05` |
| 3–5 | constants; `stop_frame=bytes([0xFE,0xFE,0x02,0x29,0xFA])`, `read_frame=bytes([0xFE,0xFE,0x02,0x20,0xFA])`; print hex |
| 6 | open `MyCobotSerialInterface` **once** |
| 7 | `measured_deg = ser.read_angles_deg(timeout_s=0.5)`; **`None` → stop, check power/port** |
| 8 | `diff_deg = measured_arr - home_deg`. Large values are fine: the arm is parked, not at zero |
| (extra) | `start_deg = list(measured_deg)` to return to the parked pose at the end |
| 9 | `target_deg = list(measured_deg); target_deg[0] += 10`, `speed = 20`; check with `check_target` (below) |
| 10 | send, wait 3 s, stop cell ready |
| 11–12 | `error_deg = target_arr - measured_after_arr`; bar plot |
| 13–14 | `ser.stop_motion()`, `ser.resume_motion()`, read back |
| (extra) | back to `start_deg` at speed 20 (only after checking the move is ~−10° on J1) |
| 15 | `ser.close()` **before** Part 2 |

Facts from the robot (2026-09-28): powered servos hold position ("motors locked") — normal, not the stop state.
Parked pose read: `[7.2, -99.31, -70.92, 81.38, 90.08, -74.26]` (folded arm). **Never send all-zeros from there**
(large motion on every joint); move one joint at a time, 5–15°, from the measured pose. Careful with J2/J3 when folded.

Joint order: J1 base · J2 shoulder · J3 elbow · J4 wrist bend · J5 wrist turn · J6 flange (index 0–5).
Safety check for any manual target (paste once, call before every `send_angles_deg`):
```python
limits = np.array([[-168, 168], [-135, 135], [-150, 150], [-145, 145], [-165, 165], [-180, 180]])  # myCobot 280 (deg)
def check_target(target_deg, max_step=15):
    cur = np.array(ser.read_angles_deg(timeout_s=0.5)); tgt = np.array(target_deg, dtype=float)
    assert tgt.shape == (6,), "need exactly 6 angles"
    assert np.all((tgt >= limits[:, 0]) & (tgt <= limits[:, 1])), f"outside joint limits: {tgt}"
    for j in range(6): print(f"J{j+1}: {cur[j]:8.2f} -> {tgt[j]:8.2f}   ({tgt[j]-cur[j]:+.2f}°)")
    assert np.all(np.abs(tgt - cur) <= max_step), f"a joint moves more than {max_step}°"
    return tgt.tolist()
```

Part 2 (tasks 16–29): launch the controller in its own SSH terminal (leave it open), then publish on `/mycobot/joint_command` (rad) and
`/mycobot/joint_velocity` (rad/s: small, short, then zeros). Start with 0.1 rad/s on one joint for 1–2 s.

PDF short questions (interview prep): purpose of serial comms; why frames; commanded vs measured; position vs
velocity mode; why validate before sending; purpose of a safety stop; why compare commanded vs measured;
why real robots need more caution than simulation.

---

## 7b. Lab 9 (final lab): Pick and Place with MoveIt

**Step-by-step commands and background: [solutions/Lab8_Lab9_run_guide.md](solutions/Lab8_Lab9_run_guide.md)** (§4 one-time
setup A0–A7, §6 simulation / real robot B1–B6 / stop / first pick and place with the camera D1–D5; also safety
surprises, why, tunable values, experiments, troubleshooting). PDF: `pdfs/Pick_And_Place-2.pdf` (Sep 23).

**Structure (PDF):** Part 0 *Explore the existing system* is required; then **2 of 5 tasks** (A–E), the rest optional.
**Approach (decided 2026-10-05): object shape detection + extension of the object interface**, in the course ROS
pipeline with the values that worked in `solutions/lab9_simple/`: **[solutions/lab9_real_hardware/README.md](solutions/lab9_real_hardware/README.md)**
(run order, Part 0, evaluation). **Own packages, course packages unchanged (since 10-05 15:45):**
`pp_moveit_ws/src/lab9_interfaces` (`GetObject.srv`) and `pp_moveit_ws/src/lab9_pick_place` (`vision_lab9`, `brain_lab9`,
`controller_lab9` for the Pi, `lab9_moveit.launch.py`, `lab9_real.launch.py`, `config/lab9.yaml`); what replaces what:
[solutions/lab9_real_hardware/COURSE_PACKAGE_CHANGES.md](solutions/lab9_real_hardware/COURSE_PACKAGE_CHANGES.md).
Status 10-05: runs on the robot (moves + home OK), full pick not yet verified; package split tested in simulation. Earlier plan
(2026-10-02, A + B or B + C): `solutions/lab9_real_hardware/old_tasks_ABC/GUIDE.md`. Single-shot fallback without
MoveIt: `solutions/lab9_simple/`. Old synthetic-data solution kept in `solutions/lab9_old_synthetic/` for reference.

**What runs where:**
- Pi: the controller only: `lab9_pick_place controller_lab9` (pump GPIO 20 + valve GPIO 21, smooth execution) or, for the
  Part 0 baseline, the course `mycobot_controller controller`. Never both.
- Lab PC: camera, vision, MoveIt, brain, RViz.
- Same branch `myCobot-lab` on both, `ROS_DOMAIN_ID=47`, `~/rosenv9.sh` in every terminal, ufw allows the other host.

| Task | Edit (course code, git keeps the original) | New files (put them in `lab9/`) | Rebuild |
|---|---|---|---|
| 0 Explore | none | report + data-flow diagram | — |
| A ArUco calibration | `mycobot_vision/vision.py` (`send_cube_coords`) | calibration script + parameters, annotated image, error table | no |
| B Robust HSV | `vision.py` (`img_callback`) | frames under 2 lightings, before/after | no |
| C HSV from examples | none (standalone tool `solutions/lab9_real_hardware/hsv_calibrate.py`) | thresholds + evaluation | no |
| D Colour + shape | `vision.py`, `mycobot_interfaces/srv/GetCubeCoords.srv` | test frames | Lab PC: interfaces, vision, brain |
| E Object interface | `GetCubeCoords.srv`, `vision.py`, `mycobot_brain/brain.py` | — | Lab PC: as D |

One commit per task. A `.srv` change is rebuilt on the Lab PC only (the Pi controller doesn't use `mycobot_interfaces`).

**First pick and place with the camera (run guide §6d), summary:**
1. No edits needed; the unchanged course code runs. The solution notebook is not used at runtime.
2. Known risk: `vision.py` maps pixels → robot with constants for the **old** camera pose
   (`rx = 0.08 + (cy−55)/280·0.15`, `ry = −0.075 + (cx−185)/280·0.15`, `z = 0.01`).
3. Before `brain`: check the image is 640×480, then measure 3 cube positions with a ruler against
   `ros2 service call /cube_coordinates …`. Error ≤ ~1 cm → run; larger → Task A (fix) or a temporary re-fit (workaround).
4. First run: menu `2` (sort), red cube, bin A. Brain moves to home on start; "rejoice" (arm straight up) after each run.
5. Record positions, choices, outcomes, the data flow and ≥ 2 limitations (Part 0 deliverable).

**Status 2026-10-01:** setup A1–A6 done (MoveIt + build on the Lab PC, controller built on the Pi, firewall verified
with UDP both ways, `rosenv9.sh` on both). **Next: A7** (multicast test), then Part D.

---

## 8. Game plan

**Phase 0 (done):** laptop setup, workspaces, repo.

**Phase 1, day 1:** kick-off, safety briefing, group. Ask the TAs the open questions in §11.

**Phase 2, Labs 1–4 (maths core, laptop):** most of the interview theory comes from these. Pre-read Siciliano
ch. 2.1–2.7 (and the kinematics chapters). Finish fast, at home if possible, and save lab time for the robot.

**Phase 3, Labs 5–7 (robot):** do all offline cells before your robot slot. In the lab, only measure/run, save data
and plots. Always small motions first, stop command ready, compare commanded vs measured.

**Phase 4, Lab 9 (+8 if required):** run the existing system first (sorting/stacking menu), write the data-flow
report, pick the 2 extensions on day 1 of this phase and split them in the group.

**Routine for every lab (this is the interview prep):**
1. **Before:** read the PDF, answer its *Short Questions* in your own words (they're basically interview questions).
2. **During:** notebook top to bottom. For LLM-generated code: you must be able to explain every line.
3. **After:** upload code + write a ½-page "interview card": goal, key formula, 1 result plot, 1 pitfall you hit.
4. Group repo **github.com/manojkumar-org/mycobot-project** (private). Rotate who drives so everyone can explain everything.

---

## 9. Rules for working on the robot

1. **A human runs every cell or command that moves the robot** (`send_angles_deg`, publishing to
   `/mycobot/joint_command`, `/mycobot/joint_velocity`, `/mycobot/ee_pose`, pymycobot moves). Automated tools only
   read files and logs, read angles, list/echo topics, build, and check ports.
2. Before any motion: workspace clear, direction understood, stop path ready, small + slow first.
3. Serial notebook and `mycobot_control` never at the same time (`fuser -v /dev/ttyAMA0`).
4. Don't commit `pdfs/`, tokens, `build/ install/ log/`, or weights. Never store the GitHub token in a file inside the
   repo (`.git/info/exclude` covers `pdfs/` and `*token*` on the laptop; add the same on the Pi).
5. Hardcoded paths (§4, §5) are known and left as-is. Change only when a lab needs it.
6. Shared Pi, end of session: push your work from the Pi, `ssh cobot 'git credential-cache exit'`, stop Jupyter/controller
   processes you started (Ctrl+C, or `kill $(cat ~/jup.pid)`), `fusermount -u ~/pi-mycobot` on the laptop.
7. Keep the Pi light. VS Code Remote-SSH is allowed, but never click "Install in SSH" for
   extensions (Pylance and Copilot filled the Pi's RAM). Notebooks: JupyterLab on the Pi + port forward.
   Pi-side VS Code settings: `~/.vscode-server/data/Machine/settings.json` (watcher excludes for build/, install/,
   log/, mycobot_description/).
8. **[Pi] steps are run by a person.** Anything that needs sudo, a token or a password, or moves the robot, is marked
   **[Pi]** in README/gameplan; Claude Code prompts for it with the exact commands and waits for the output.

---

## 10. Known issues (audit 2026-09-28)

- `mycobot_description` duplicated in two workspaces (277 MB each); 6 unused robot variants, 57 MB STEP file.
- TODO `description`/`license` in 7 `setup.py` and 5 `package.xml`; no top-level LICENSE.
- Bare `except:` in `pp_moveit_ws/src/mycobot_280pi/mycobot_280pi/listen_real_service.py:40,51`.
- Lab 1 notebook, task 26: run cells are in the wrong order (`ani_psi` before `ani_theta`); run theta first.
- Lab 1 notebook, task 11: compare with `np.isclose`, not `==` (floating-point noise makes `==` fail).
- `/dev/serial0` doesn't exist on this Ubuntu Pi image (no udev rule); robot code for Labs 7–9 opens it
  (`mycobot_control.launch.py:13`, `mycobot_control.py:29`, `pi_motion3_node.py:41`, `motion_node.py:119`,
  `controller.py:16`). Fix: udev link (README setup step 2), code left unchanged.
- Every `ssh cobot` command prints `setlocale: LC_ALL: cannot change locale (en_US.UTF-8)`: laptop sends the locale,
  the Pi lacks it. Harmless; fix with **[Pi]** `sudo locale-gen en_US.UTF-8`.
- `pdfs/Serial_Communication_Robot_Control.pdf` was committed in `7621d81` (pushed; private repo). Untrack with
  `git rm --cached -r pdfs/` if course PDFs shouldn't be in the repo.

---

## 11. Open questions for the TAs

1. Is Lab 8 (YOLO, April PDF) still required, or only Lab 9 (MoveIt, Sep 23 PDF)? The 25.09 intro slides only show Lab 9.
2. Which `ROS_DOMAIN_ID` should our group use? Several robots on one network otherwise see each other's topics.
3. Where do we get `mycobot_280_gazebo.urdf` (and the optional `pointcloud.mat` for Lab 1)?
4. Pi (Ubuntu 24.04.5, ROS Jazzy): may we add swap (1.8 GB RAM, no swap) and the `/dev/serial0` udev rule?
5. Upload deadlines, interview date and format; is this a 2-week block?
6. Labs 2, 8, 9: which nodes are meant to run on the Pi and which on the laptop? The camera is on the laptop and the Pi
   (1.8 GB) has no MoveIt. Does ROS 2 discovery between laptop and Pi work on the lab network (multicast), and with
   which `ROS_DOMAIN_ID` (Q2)?

---

## 12. Progress log

| Date | Done |
|---|---|
| 2026-09-27 | Course zips unpacked into 3 workspaces; day-0 plan. |
| 2026-09-28 | Laptop: ROS 2 Jazzy + rosdep, `ros2_ws` built. Repo on GitHub (branch `myCobot-lab`). Repo audit. Lab 1 solutions worked through and verified (tasks 1–7 explained in detail; 8–33 solved). Lab 7 PDF read; robot is only reachable via the Pi over SSH (`cobot@129.217.130.85`). Pi setup started (token, clone). GAME-PLAN.md merged into this file. VS Code remote extensions on the Pi filled its RAM and hung it (SSH banner timeouts); removed them, work from the laptop (§6c). |
| 2026-09-28 (afternoon) | Pi: venv + JupyterLab, opened in the laptop browser through an SSH tunnel. **Lab 7 Part 1 tasks 1–8 done**: port opened, six angles read (parked pose), difference from home computed. Tasks 9–15 code prepared (joint 1 +10°, `check_target`, return to `start_deg`). README cleaned (bring-up table, one-time setup, troubleshooting). |
| 2026-09-29 | Laptop env complete: venv sees system packages, `ipympl` installed, `ros2_ws` built, smoke test and `pip check` pass. README rewritten (Pi Start / Stop steps). `solutions/` written: worked solutions with explanations for Labs 1–9 (see `solutions/README.md`; Lab 7/8 run against a simulated robot by default, Lab 9 is the algorithmic core on synthetic data). |
| 2026-09-30 | Branch workflow: `myCobot-personal` (home edits) fast-forwarded into `myCobot-lab`; Pi pulled to `070cdf2`. Laptop SSH key + `cobot` alias with connection reuse. Pi checked: Ubuntu 24.04.5, ROS Jazzy, robot UART `ttyAMA0` = `serial0` alias, but no `/dev/serial0` link on Ubuntu → udev rule (README setup step 2). README: "How it runs" architecture, `ssh cobot`, `ttyAMA0`, **[Pi]** markers. **[Pi]** udev link `/dev/serial0 -> ttyAMA0` created and verified. Per-lab Pi software checked (§2); camera found on the laptop; Labs 3–5 won't run on the Pi. |

| 2026-10-01 | Lab 7 Part 2 and **Lab 8 done** on the robot (Pi: `python3-rpi-lgpio` for `RPi.GPIO`, `ros-jazzy-control-msgs`). Branches merged: personal = lab = `79dcab8`; both lab machines on `myCobot-lab`. Lab 9 setup A1–A6 done (§7b); `lab9_runbook.md` written (Parts A–D; since merged into `solutions/Lab8_Lab9_run_guide.md`). |

**Next:** Lab 9: A7 multicast test → guide §6d (accuracy check, then first sort run) → Part 0 report → choose
the 2 tasks (§7b) → Lab 7/8 PDF short questions.
