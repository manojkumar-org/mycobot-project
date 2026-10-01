# Lab 8 and Lab 9: running the system, what runs where, and the values to experiment with

How to read the marks in this guide:
- **[code]**: read in the source files of this repo (file and function named).
- **[check]**: could **not** be verified from the laptop (no access to the Pi); the command that answers it is given. Do not trust these until you ran the command.
- **[MOVES]**: this command or action moves the arm. A person runs it, with the workspace clear, the stop within reach, and the first move small and slow.

**Lab day in ten steps** (details in the sections named):
1. Laptop: `ssh cobot 'hostname'` works without a password (§4.1). If not, do the key setup first.
2. Laptop: run the read-only probe block (§4.2). Write down: ROS distro, whether `pymycobot` / `MyCobot280` / `RPi.GPIO` import, **where the camera is plugged in**, who holds `/dev/serial0`.
3. Ask the TAs: the group's `ROS_DOMAIN_ID`, whether Lab 8 is still required, where `mycobot_280_gazebo.urdf` is (gameplan §11).
4. Laptop (can be done at home, no robot): install the MoveIt packages and build `pp_moveit_ws` (§4.4).
5. Pi: stop Jupyter, build only `mycobot_controller` with one worker (§4.4).
6. Both machines: `~/rosenv9.sh` with the **same** domain id; multicast test (§4.3).
7. Laptop, **simulation first**: vision with `publish_test_image.py`, then `brain_simulation.launch.py` in RViz (§6a).
8. Real robot, in this order (§6b): controller on the Pi → `ros2 topic echo /joint_states --once` on the laptop → `move_group` → camera → `vision` → check coordinates with `ros2 service call` → `brain` **last** (it moves the arm to home as soon as it starts).
9. First cycle: one cube near the centre, bin A, hand at the power switch; remember the all-zero "rejoice" move after the run (§0 item 2).
10. Stop in the order of §6c; push your work; `ssh cobot 'git credential-cache exit'`.
Lab 8 notebook only: §5a (needs just the Pi and Jupyter).

Contents: 0 Safety and surprises · 1 The two systems · 2 Which machine runs what · 3 Files each machine needs · 4 Lab day: SSH to the Pi, probes, builds, network ·
5 Lab 8 runbook · 6 Lab 9 runbook · 7 Why it is built this way · 8 Values you can change · 9 Experiments, safest first · 10 Troubleshooting · 11 Problems found in the code

---

## 0. Safety, and eight things the code does that you would not expect

Rules that apply to everything below: a person runs every command that moves the arm; workspace clear; know where the power switch is *before* the first run; first run in simulation where possible; small and slow first; only **one** program may hold `/dev/serial0` (`fuser -v /dev/serial0` shows who).

| # | What happens | Where [code] | What to do |
|---|---|---|---|
| 1 | **Starting `brain` moves the arm** to the home pose `[0.16, -0.06, 0.32, 0, 1.57, 0]` before the menu even appears. | `brain.py: control_menu()` calls `go_home()` first | Start `brain` last, workspace clear, hand at the power switch. |
| 2 | **After every sort or stack run the controller sends all-zero joint angles** (arm straight up) at speed 40, then `[0,-60,15,-45,0,0]`, then zeros again. `brain.rejoice()` publishes `True` on `/rejoice`; `controller.rejoice` runs three `send_angles` with fixed sleeps. | `brain.py: rejoice()`, `controller.py: rejoice()` | Clear the space above the arm. If you do not want it: remove the two `self.rejoice()` calls in *your copy* of `brain.py` (it is a course file: ask the TAs first). Never publish `True` on `/rejoice` yourself. |
| 3 | **Starting the Lab 8 `motion_node` moves the arm** to the intermediate pose, then home, at once. | `motion_node.py: __init__` ends with `self.go_home()` | Same as 1. |
| 4 | The Lab 8 stop key `s` is **disabled by default** (`DEBUG_STOP_ENABLE = False`). Ctrl+C in `brain` only ends the Python process; a trajectory already sent to the controller still runs to its end (the controller has no cancel handler). | `motion_node.py`, `controller.py: execute_trajectory` | Do not rely on software stops. The power switch is the stop. |
| 5 | Lab 8 drives **two** GPIO pins for the pump (20 = vacuum motor, 21 = release valve); the Lab 9 controller drives **only pin 20**. Pin 21 is never set up there, so the valve is whatever the hardware defaults to. | `motion_node.py: pump_on/pump_off`, `controller.py: control_pump` | **[check]** If suction is weak or the cube does not drop in Lab 9, compare with Lab 8's `pump_on` (both pins LOW) before blaming the vision. |
| 6 | The Lab 9 pump is only switched by a topic: `ros2 topic pub /pump_controller std_msgs/msg/String "{data: 'on'}"` runs the motor. | `controller.py: control_pump` | Test the pump with an object at the nozzle, motor on for seconds, then `off`. |
| 7 | The controller sends `speed = int(100 * max|velocity|)` for every trajectory point. MoveIt's joint velocity limit is 2.0 rad/s and `brain` asks for scaling 1.0, so the value can reach 200, but the robot API takes 0–100. | `controller.py`, `joint_limits.yaml`, `brain.py: send_goal_pose` | **[check]** What the library does with values above 100 and with 0 (short segments). Watch the controller log in the simulation first; experiment 9.7. |
| 8 | `brain.launch.py` and `brain_simulation.launch.py` open **gnome-terminal tabs**. They need a desktop session; over plain SSH or tmux they fail. They also do **not** start the controller. | `brain.launch.py` | On the Pi: start the nodes by hand (section 6). |

---

## 1. The two systems

### Lab 8: one process per job, direct robot library, no MoveIt
```
 USB camera ─► vision_node (YOLO pose + solvePnP) ──/detected_objects──► motion_node ──► pymycobot ──► arm
              (pp_yolo_ws/src/vision)           mycobot_msgs/DetectedObject   (pp_yolo_ws/src/mycobot_motion_v1)   └► GPIO 20/21 ─► pump
```
- `DetectedObject`: `float32 x, y, z` (**metres**, robot base frame), `string color` (+ joint fields `j1..j6`, unused by the vision node). **[code]**
- `motion_node` filters by workspace, waits 2 s collecting detections, picks the highest stack (then colour priority), and runs the 8-step sequence of the Lab 8 notebook, in **millimetres and degrees**. **[code]**
- The Lab 8 notebook (`PickAndPlaceTemplate.ipynb`) rebuilds the pieces of this by hand; it does **not** need ROS.

### Lab 9: five nodes, MoveIt plans, the controller executes
```
 USB camera                                                       ┌──────────── MoveIt move_group ─────────────┐
    │ camera/image (10 Hz)                                         │ /move_action (pose goals, plans + executes)│
    ▼                                                              │ /compute_cartesian_path (straight lines)   │
 opencv_camera ─► Vision ──/cube_coordinates (service)──► Brain ───┤ /collision_object, /attached_collision_object (planning scene)
 (mycobot_280pi)  (HSV, pixel→robot)   GetCubeCoords      (menu,   └───────────────┬────────────────────────────┘
                                                           sequences)              │ /arm_group_controller/follow_joint_trajectory (action)
                                                              │ /pump_controller   ▼
                                                              └──(String "on"/"off")──► Controller (Pi) ─► pymycobot ─► arm,   GPIO 20 ─► pump
                                            Controller ──/joint_states (20 Hz)──► MoveIt (current state)
```
- Free-space moves: `Brain → /move_action → MoveIt plans and executes → controller`. Straight-line moves (down onto the cube, back up): `Brain → /compute_cartesian_path → Brain sends the returned trajectory directly to the controller` (MoveIt has no action to execute Cartesian paths). **[code]**
- The RViz simulation (`demo.launch.py`) **replaces** the controller (it serves the same action). Never run both. **[code, MoveIt README]**
- Units: Vision/Brain/MoveIt in **metres and radians**, frame `g_base`. The controller converts to what pymycobot needs.

---

## 2. Which machine runs what

| Machine | Runs | Why |
|---|---|---|
| **Robot Pi** `cobot-pi1` | `controller` (Lab 9); the Lab 8 notebook and `motion_node` | Only the Pi has `/dev/serial0` (robot) and the GPIO header (pump). The controller README says it must run on the Pi. **[code]** |
| **Laptop or lab PC** | MoveIt `move_group`, `brain` (interactive menu), `vision` (opens an OpenCV window), RViz, the camera node (if the camera is plugged in there) | 1.8 GB RAM and no swap on the Pi (gameplan §2); vision and RViz need a display; the menu needs a terminal. |
| **Lab 8 YOLO vision** | laptop or lab PC | needs `torch` and `ultralytics` (hundreds of MB), which do not fit the Pi's RAM budget. `pp_yolo_ws/Vision_requirements/requirements.txt` pins torch 2.9.1. |

**Where is the camera plugged in? [check]** This decides where the camera node runs. Find out on the Pi and on the other machine: `v4l2-ctl --list-devices` (needs `sudo apt install v4l-utils`) or `ls /dev/video*`.
- Camera on the **laptop or lab PC**: everything except the controller runs there (the original design; `opencv_camera` has a `num` parameter for the device index).
- Camera on the **Pi**: run `opencv_camera` on the Pi (it needs `mycobot_280pi` and `cv_bridge` built there) and send `camera/image` over the network: 640×480×3 bytes × 10 Hz ≈ 9 MB/s ≈ 74 Mbit/s. Use a wired connection; with Wi-Fi expect dropped frames. Alternative: run `vision` on the Pi and look at its window through `ssh -X` (heavy for the Pi).
- Whatever you choose, `vision.py` assumes a **640×480** image (its pixel constants and the Lab 8 intrinsics are for that size). Check: `ros2 topic echo camera/image --once --field width` and `--field height`.

**ROS networking between the machines [check].** Nodes on different machines find each other with DDS multicast, but only with the **same `ROS_DOMAIN_ID`** on every machine and a network that passes multicast. Open question for the TAs (gameplan §11 #2): which domain id is yours. Test in section 4.5.

---

## 3. Files each machine needs

Repo path: `~/mycobot-project` on the Pi and the lab PC; `~/TUD/cobots` on this laptop. Same repo, branch `myCobot-lab`.

### Robot Pi
| Needed for | Files / packages | Notes |
|---|---|---|
| Lab 8 notebook | `PickAndPlaceTemplate.ipynb` (work), `solutions/Lab8_PickAndPlace_solution.ipynb` (compare), the venv `~/venvs/mycobot` with JupyterLab | `pymycobot` and `RPi.GPIO` importable **[check]**; no ROS needed |
| Lab 8 `motion_node` | `pp_yolo_ws/src/mycobot_msgs`, `pp_yolo_ws/src/mycobot_motion_v1` (built); or the older `ros2_ws/src/mycobot_control/pi_motion3_node.py` (run as a script, imports `mycobot_msgs`) | ask the TAs which one is current; `motion_node.py` imports `termios`, so it needs a terminal |
| Lab 9 controller | `pp_moveit_ws/src/mycobot_controller` (built with colcon) | needs `control_msgs`, `pymycobot` (module `pymycobot.mycobot280`), `RPi.GPIO` **[check]** |
| Network | same `ROS_DOMAIN_ID` as the other machine | section 4.5 |

**Not on the Pi:** MoveIt, RViz, torch/ultralytics, or VS Code extensions installed "in SSH" (gameplan §9 rule 7).

### Laptop / lab PC
| Needed for | Files / packages | Notes |
|---|---|---|
| Lab 9 nodes | `pp_moveit_ws/src/{mycobot_interfaces, mycobot_description, mycobot_280_moveit2, mycobot_280pi, mycobot_vision, mycobot_brain}` built with colcon | the controller is **not** built here unless you test the real-hardware imports |
| ROS and MoveIt packages | **This laptop has none of the MoveIt packages installed** (checked: 0 `moveit` packages, no `control_msgs`, `moveit_msgs`, `controller_manager`, `joint_state_publisher_gui`, `xacro`) | install block in 4.4; run with `sudo` yourself |
| Camera | a USB camera and `v4l-utils` **or** `solutions/publish_test_image.py` (no camera needed) | |
| Lab 8 YOLO vision | `pp_yolo_ws/src/{vision, mycobot_msgs}`, `pp_yolo_ws/weights/best.pt` (42 MB, never commit), a venv `yolovenv` from `Vision_requirements/requirements.txt` (numpy 2.x, torch) | three hardcoded paths to edit in your copy: weights `/home/tejas/YOLO/runs/pose/train/weights/best.pt`, `CALIB_FILE /home/tejas/z_scale_calibration.json`, camera `/dev/video2` |
| Your tools | `solutions/hsv_calibrator.py`, `solutions/publish_test_image.py`, `solutions/lab9_synthetic.py`, the two notebooks | |

One more constraint **[code]**: `mycobot_description` exists in **both** `ros2_ws` and `pp_moveit_ws` (277 MB each, same package name). In one terminal source **only one** workspace overlay; for Labs 8 and 9 that is `pp_moveit_ws`/`pp_yolo_ws`, not `ros2_ws`.

---

## 4. Lab day: from the laptop to the Pi

Everything in 4.1 and 4.2 only **reads** (no motion): safe to run at any time.

### 4.1 Once: key and alias (gameplan §6c)
```bash
ssh-keygen -t ed25519                      # press Enter for defaults
ssh-copy-id cobot@129.217.130.85           # asks for the Pi password once
```
Add to `~/.ssh/config` on the laptop:
```
Host cobot
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
Test: `ssh cobot 'hostname; uptime'` → `cobot-pi1`.

### 4.2 Read-only probe of the Pi (copy the whole block)
```bash
ssh cobot 'bash -s' <<'EOF'
echo "== system";   hostname; lsb_release -ds; uname -m; free -h | head -2
echo "== ROS";      ls /opt/ros; D=$(ls /opt/ros | head -1); source /opt/ros/$D/setup.bash; echo "ROS_DISTRO=$ROS_DISTRO ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-unset}"
ros2 pkg list 2>/dev/null | grep -E '^(control_msgs|cv_bridge|rclpy|sensor_msgs)$'
echo "moveit packages: $(ros2 pkg list 2>/dev/null | grep -c moveit)"
echo "== python";   ~/venvs/mycobot/bin/python -c "import pymycobot; print('pymycobot', pymycobot.__version__)"
~/venvs/mycobot/bin/python -c "from pymycobot.mycobot280 import MyCobot280; print('MyCobot280 import ok')"
~/venvs/mycobot/bin/python -c "import RPi.GPIO as G; print('RPi.GPIO', G.VERSION)"
echo "== hardware"; ls -l /dev/serial0; groups; ls /dev/video* 2>&1 | head; v4l2-ctl --list-devices 2>&1 | head -12
echo "== who holds the port"; fuser -v /dev/serial0 2>&1
echo "== repo";     cd ~/mycobot-project && git status -sb | head -3; ls pp_moveit_ws/src pp_yolo_ws/src 2>&1 | head -20
EOF
```
What the answers mean:

| Output | Meaning / next step |
|---|---|
| `ls /opt/ros` empty or missing | No ROS on the Pi: the controller cannot run there. Ask the TAs (gameplan §11 #4). The Lab 8 notebook still works. |
| `ROS_DISTRO=jazzy` | Matches the laptop. A different distro: build and run everything against the Pi's distro and expect interface differences. |
| `control_msgs` missing | `sudo apt install ros-<distro>-control-msgs` (you run sudo). |
| `moveit packages: 0` on the Pi | Expected and fine: MoveIt runs on the laptop. |
| `MyCobot280 import ok` fails | The Pi's pymycobot is too old for `controller.py`. `pip install -U pymycobot` **inside the venv**; the laptop venv has 4.0.7. |
| `RPi.GPIO` import fails | The pump cannot be driven from Python. On Ubuntu 24.04 the compatible package may be `rpi-lgpio` or `python3-rpi.gpio`. Ask the TAs which one the lab uses. |
| `v4l2-ctl: command not found` | `sudo apt install v4l-utils`; or use `ls /dev/video*` (there are usually two nodes per camera; the lower index is the video one). |
| `fuser` lists a process | Something already holds the robot port: stop that first (Jupyter serial notebook, `mycobot_control`, a controller). |

### 4.3 Network between the two machines
1. Both machines on the same subnet: `ping -c 3 <other machine>`.
2. Decide the domain id (TA answer); then on **both**: `export ROS_DOMAIN_ID=<n>` (also `unset ROS_LOCALHOST_ONLY`).
3. Multicast test (works only if ROS is installed on both): on the laptop `ros2 multicast receive`, on the Pi `ros2 multicast send`. If the message does not arrive, DDS discovery will not work: ask the TAs (or fall back to running everything on one machine).
4. Later, once the controller runs on the Pi: on the laptop `ros2 topic list` must show `/joint_states`, and `ros2 topic echo /joint_states --once` must print six joint values.

### 4.4 Build and install
**Laptop (needs `sudo` once).** The MoveIt config lists these dependencies **[code, package.xml]**; the apt names follow the rosdep keys **[check]**:
```bash
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-configs-utils ros-jazzy-moveit-msgs ros-jazzy-control-msgs \
     ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-controller-manager ros-jazzy-joint-trajectory-controller \
     ros-jazzy-joint-state-publisher-gui ros-jazzy-robot-state-publisher ros-jazzy-xacro ros-jazzy-tf2-ros \
     ros-jazzy-warehouse-ros-mongo ros-jazzy-joy python3-tk ros-jazzy-cv-bridge python3-colcon-common-extensions v4l-utils tmux
```
If a name is not found, `rosdep` can resolve the rest from the package files (`gazebo_ros_control` in `package.xml` has no Jazzy package of that name; skip it, nothing in the launch files uses it **[check]**):
```bash
cd ~/TUD/cobots/pp_moveit_ws && rosdep install --from-paths src --ignore-src -r -y --skip-keys "gazebo_ros_control python3-pymycobot python3-rpi.gpio"
```
Build (**do not** have the venv active; the build must use the system Python):
```bash
source /opt/ros/jazzy/setup.bash
cd ~/TUD/cobots/pp_moveit_ws
colcon build --symlink-install --packages-up-to mycobot_brain mycobot_vision mycobot_280_moveit2 mycobot_280pi
source install/setup.bash
ros2 pkg list | grep mycobot          # expect: mycobot_280_moveit2, mycobot_280pi, mycobot_brain, mycobot_description, mycobot_interfaces, mycobot_vision
```
**Pi (controller only).** With Jupyter **stopped** (RAM), one worker:
```bash
ssh cobot
tmux new -s build
source /opt/ros/$(ls /opt/ros | head -1)/setup.bash
cd ~/mycobot-project/pp_moveit_ws
colcon build --symlink-install --parallel-workers 1 --packages-select mycobot_controller
```
(After `git pull` on the Pi if the sources changed. `--symlink-install` means later edits to the Python files take effect without rebuilding.)

### 4.5 One environment file per machine
`~/rosenv9.sh` (laptop; on the Pi use its distro and path):
```bash
source /opt/ros/jazzy/setup.bash
source ~/TUD/cobots/pp_moveit_ws/install/setup.bash        # Pi: ~/mycobot-project/pp_moveit_ws/install/setup.bash
export ROS_DOMAIN_ID=<your group's id>                      # identical on every machine
unset ROS_LOCALHOST_ONLY
```
In every terminal first `source ~/rosenv9.sh`. Use the venv (`source ~/venvs/mycobot/bin/activate`) only for notebooks and the helper scripts; it has system site packages, so `rclpy` works there too.

---

## 5. Lab 8 runbook

### 5a. The notebook route (needs only the Pi) [MOVES, when you switch it on]
1. Stop anything that holds the serial port (`fuser -v /dev/serial0`): the Lab 7 notebook (`ser.close()`), `mycobot_control`.
2. Start Jupyter on the Pi as in README → *Robot Pi → Start*; open `PickAndPlaceTemplate.ipynb`.
3. Work through the tasks. **Every motion cell is gated by a flag** (`enable_motion`, `enable_pump_test`) that is `False` in the template. Flip one at a time, with the workspace clear.
4. Order that is easiest on the hardware: Task 1 (connect) → 6–8 (GPIO and pump with an object held at the nozzle) → 9 (`go_home`) → 11 (one move) → 13 (full sequence, one cube at (150, 0), cube on the table) → 25–26.
5. In `solutions/Lab8_PickAndPlace_solution.ipynb` set `USE_REAL_HARDWARE = True` **only on the Pi**; on the laptop leave it `False`: it then prints what would be sent, with simulated times, and nothing moves.

### 5b. The ROS route (optional; ask the TAs whether Lab 8 is still required)
Needs three terminals on two machines. Order matters because `motion_node` moves on start.
1. **Laptop:** vision (needs the three edited paths of section 3):
   ```bash
   source ~/yolovenv/bin/activate && source /opt/ros/jazzy/setup.bash && source ~/TUD/cobots/pp_yolo_ws/install/setup.bash
   ros2 run vision vision_node
   ```
   First start: no calibration file, so it enters **calibration mode** (a window "Z-Scale Calibration"): place **one cube** (any colour) in the workspace, click the window and press `c` to capture a sample; it needs **5 samples with the cube in different positions** (the depth scale of Task 19); `r` resets the samples, `q` quits without calibrating. The result is written to `CALIB_FILE`, so later starts skip this step. **[code]**
2. **Check, no motion:** `ros2 topic echo /detected_objects` shows `x, y, z, color` in metres for cubes in view.
3. **Pi:** [MOVES immediately: intermediate pose, then home] `ros2 run mycobot_motion_v1 motion_node`. It waits for detections, collects them for 2 s, picks and sorts. Stop key `s` only works if you set `DEBUG_STOP_ENABLE = True`.
4. End: Ctrl+C both. `motion_node` calls `GPIO.cleanup()` only after `spin()` returns normally; after Ctrl+C it may be skipped **[check]**, so the pins can stay as they were (the pump driver is switched off by `pump_off` after every cycle, so this is mostly harmless).

---

## 6. Lab 9 runbook

### 6a. Without the robot (laptop only): start here
**Vision experiments with no camera and no robot** (safe, and where most extension work happens):
```bash
# terminal 1
source ~/rosenv9.sh
python3 ~/TUD/cobots/solutions/publish_test_image.py --scene shapes     # or a saved frame: publish_test_image.py frame.png
# terminal 2
source ~/rosenv9.sh
ros2 run mycobot_vision vision                                         # window "Color Detection" with the mouse HSV overlay
# terminal 3: ask the service (no motion)
source ~/rosenv9.sh
ros2 service call /cube_coordinates mycobot_interfaces/srv/GetCubeCoords "{color: red}"
```
The answer is `coords=[x, y, z, roll, pitch, yaw]` in metres/radians, or six times `1.0` for "not detected". `publish_test_image.py` sends a synthetic scene (from `lab9_synthetic.py`) at 10 Hz as `camera/image`; with a real camera use `ros2 run mycobot_280pi opencv_camera --ros-args -p num:=0` instead (index from `v4l2-ctl --list-devices`).

**Motion in RViz (simulation, no robot, no controller):** [no physical motion]
```bash
source ~/rosenv9.sh
ros2 launch mycobot_brain brain_simulation.launch.py     # opens 4 gnome-terminal tabs: Brain, MoveIt demo (RViz), OpenCV camera, Vision
```
It needs a desktop and a camera at index 0; without a camera, replace the OpenCV tab by `publish_test_image.py` (start the other three by hand). The RViz demo contains the table, the bins and cubes, and serves the same trajectory action as the real controller. In the Brain tab you get the menu (below). **Do not start the real controller while the simulation runs.**

### 6b. With the robot [MOVES]
Start order and what to look for. Use `tmux` on the Pi, separate terminals on the laptop.

| # | Where | Command | Expect |
|---|---|---|---|
| 1 | **Pi** (`tmux new -s ctl`) | `source ~/rosenv9.sh && ros2 run mycobot_controller controller` | logs `Joint state publisher ready!`, `Pump ready!` (pin 20 set HIGH = pump off), `FJT action server ready!`, `Current coordinates: [...]`. No motion yet. |
| 2 | laptop | `source ~/rosenv9.sh && ros2 topic echo /joint_states --once` | six joint values from the Pi: the network works. |
| 3 | laptop | `ros2 launch mycobot_280_moveit2 move_group.launch.py` | MoveIt's usual last line `You can start planning now!` **[check]**; no errors about a missing robot description |
| 4 | laptop | `python3 ~/TUD/cobots/solutions/publish_test_image.py` **or** `ros2 run mycobot_280pi opencv_camera --ros-args -p num:=<index>` | `ros2 topic hz camera/image` ≈ 10 Hz |
| 5 | laptop | `ros2 run mycobot_vision vision` | window with rectangles on the cubes, and `Cube coordinate service ready!` |
| 6 | laptop | the `ros2 service call ...` of 6a for each colour you will use | coordinates plausible for where the cubes are (x 0.08…0.23, y −0.075…0.075 for the old mapping) |
| 7 | laptop, **brain last** | `ros2 run mycobot_brain brain` | it waits for four servers (`... ready!` lines), then **moves the arm to home**, then shows the menu |

Menu **[code]**: `1` stack (green on red, then blue on green; yellow is commented out), `2` sort. Sort asks `Select Cube to Pick: red (r), yellow (y), green (g), blue (b)`, picks it, then `Select Bin to Drop: A, B, C, D`; `exit` goes back to the top. The first moves under supervision: choose a cube near the centre of the workspace and bin A. After **each** run, section 0 item 2 (`rejoice`) happens.

### 6c. Stopping
1. Menu: `exit`, then Ctrl+C in the brain terminal (it switches the pump off and removes the cubes from the planning scene in its `finally`).
2. Ctrl+C vision, camera, MoveIt. 3. On the Pi: Ctrl+C the controller (it calls `GPIO.cleanup()`), then `exit` the tmux session. 4. Push your work from the Pi if you changed files there, `ssh cobot 'git credential-cache exit'`.
Emergency: the arm's power switch (section 0, item 4).

---

## 7. Why it is built this way

- **Controller on the Pi, brain and MoveIt elsewhere.** Hardware access (serial, GPIO) is local to the Pi. MoveIt plans in seconds on a laptop and would take most of the Pi's 1.8 GB. The only things crossing the network are small messages (`/joint_states` at 20 Hz, trajectories, pump strings). The camera image is the one big stream: keep the camera node and Vision on the same machine.
- **Vision answers a service instead of publishing continuously.** The Brain asks "where is the red cube?" at the moment it needs it: simple, and the answer is always the latest frame. It is a **single measurement**: the Brain does not update the grasp pose while approaching (the PDF calls this single-measurement PBVS). Hence the accuracy of the pixel-to-robot map is decisive.
- **HSV segmentation + rectangle test (Lab 9)** instead of a neural network (Lab 8): fast on a laptop CPU, no training data, easy to inspect (mouse overlay). The price: sensitive to lighting, one object per colour, and only squares. Lab 8's YOLO + keypoints + `solvePnP` gives a 3D pose and handles stacks, but needs torch and a depth calibration.
- **Two kinds of motion.** `move_action` (pose goal with collision checking) for the long moves; `compute_cartesian_path` (straight line, `max_step` 1 cm) for the short vertical approach and retreat, because a straight line avoids hitting the cube sideways and a pose goal does not guarantee the path.
- **Hover first.** Pick: hover 10 cm above → straight down 5 cm → pump on → straight up 10 cm. A vertical approach tolerates a few millimetres of detection error; a sideways approach would knock the cube.
- **Collision objects follow the cube.** A cube is first attached to the table (so cubes do not "collide" with each other in the scene), then re-attached to `pump_head` when picked, so the planner moves the arm *with* the cube, then back to the table when released.
- **The pump is a topic.** One `std_msgs/String` (`"on"`/`"off"`): a `Bool` was tried and abandoned because almost any input was read as true (comment in `controller.py`).
- **The controller replays waypoints open loop.** For each trajectory point it sends the joint angles and sleeps for the time to the next waypoint; it never checks that the arm arrived. Simple, but timing errors accumulate and nothing detects a stalled joint.
- **The Lab 8 sequence uses fixed sleeps too** (`MOTION_SLEEP = 1.5 s`): a slower move would be cut short by the next command. That is why a speed increase must go together with a check of the sleeps.

---

## 8. Values you can change

Rule for every change: **one value at a time**, write down old → new and what you observed, try it in the simulation or without the cube first. "Try" is guidance from the geometry, not a verified limit, and the "Why" columns are my reading of the code and the PDF, not statements from the course authors: the TAs can confirm them.

### 8.1 Lab 8 (`motion_node.py` and notebook)
| Value | Now | Why this value | Try | Effect / watch for |
|---|---|---|---|---|
| `MOVE_SPEED` | 50 | middle of the 1–100 range: fast enough, not violent | 20 → 70 | slower = more reliable approach; faster = the 1.5 s sleep may no longer cover the move |
| `MOTION_SLEEP` | 1.5 s | so that a plain move at speed 50 has probably finished before the next command (an assumption, not measured here) | 1.0 → 3.0 | too short: the next command interrupts the move; too long: the cycle is slow (19 s per cube today) |
| `NOZZLE_LENGTH_MM` | 68 | length of the suction cup from the flange (Lab 5 TCP, applied by hand) | ± 5 mm | wrong value: nozzle stops in the air or presses on the cube |
| `HOVER_MARGIN` | 70 mm | clearance above the pick height | 40 → 100 | smaller: hits the neighbours; bigger: longer moves |
| `DROP_Z_MM` | 60 mm | release height above the bin | 40 → 100 | too high: cube falls and bounces; too low: collides with the bin |
| `WORKSPACE_*` | x 75…225, y −75…75 mm | most likely the part of the table the camera sees reliably and the arm reaches | shrink | a smaller box is safer; enlarging beyond the camera view gives wrong positions |
| `HOME_COORDS`, `INTER_COORDS`, `HOME_SPEED`, `HOME_DELAY` | see notebook Task 3; 40; 4 s | home is the camera-viewing pose; the waypoint turns the wrist gradually | do not change without measuring | wrong poses can hit the table or the camera mount |
| `DETECTION_WAIT_TIME` | 2.0 s | collect several frames before choosing (flicker, stacks) | 0.5 → 4 | shorter: may miss a higher-priority cube; longer: slow |
| `BIN_COORDS`, `COLOR_PRIORITY` | notebook Tasks 5, 14 | the bins' measured positions; red first | swap priorities | no risk; check the bins are where the table says |
| vacuum timing in `pump_off` | 0.3 s then 2.0 s | let the motor stop, then vent and let the cube drop | 1.0 → 3.0 s | too short: the arm leaves with the cube stuck to the cup |
| vision `CONF_THRESH` | 0.75 | reject weak YOLO detections | 0.5 → 0.9 | lower: false positives; higher: missed cubes |
| `Z_ONE_CUBE`, `CUBE_HEIGHT` | 0.36 m, 0.04 m | depth of a one-cube top face from the camera; cube size | re-measure | wrong → every stack level and height is off (Tasks 19–20) |
| `t_base_cam`, `R_base_cam`, camera matrix | `[0.170, 0, 0.39]` m; swap-and-flip; `fx 756.8, fy 751.6, cx 327.9, cy 224.3` | calibrated for the previous camera pose | re-calibrate (Lab 9 task A method) | a shifted camera moves every detection by the same offset |

### 8.2 Lab 9 vision (`vision.py`, `opencv_camera.py`)
| Value | Now | Why | Try | Effect / watch for |
|---|---|---|---|---|
| HSV ranges | red `0–15`/`170–200`, yellow `16–55`, green `56–80`, blue `81–110`; `S ≥ 100`, `V ≥ 100` (**blue: S, V ≥ 200**) | hue picks the colour; S and V reject grey and dark; red wraps around 0 | use the mouse overlay and `hsv_calibrator.py`; `V ≥ 50` | hue is 0–179 in OpenCV (`200` is invalid); a too strict V loses cubes in shadow; too loose accepts the table |
| side length | 50…150 px | a 4 cm cube at this camera height | measure | smaller min: noise passes; larger max: merged cubes pass |
| aspect ratio | ≥ 0.75 | a square top is ≈ 1; allows perspective | 0.7 → 0.9 | too strict: tilted cubes lost; too loose: rectangles pass |
| pixel → robot | `x = 0.08 + (cy−55)/280·0.15`, `y = −0.075 + (cx−185)/280·0.15`, `z = 0.01` | linear map fitted to four corner points of the **previous** camera pose | replace by the Task A calibration | systematic offset if the camera moved: measure with a ruler |
| `camera/image` rate, `num` | 10 Hz (timer 0.1 s), device 0 | enough for static cubes | `-p num:=2` | wrong index: `The camera was successfully turned on!` never appears |
| mask cleanup (Task B) | none in the original; 7×7 ellipse in the solution | removes isolated pixels and bridges 3–4 px gaps | 5 → 11 | bigger: rounds the cube, can delete small cubes |

### 8.3 Lab 9 brain and MoveIt (`brain.py`, `mycobot_280_moveit2/config`)
| Value | Now | Why | Try | Effect / watch for |
|---|---|---|---|---|
| hover above cube | `z + 0.10` | clearance for a vertical approach | 0.08 → 0.15 | lower: risk of hitting the cube; higher: longer Cartesian move |
| descent | `−0.05` (pump head ends at `z + 0.05`) | with `z = 0.01` the pump head stops 2 cm above the cube's top face | change **together with** the returned z | see Task A step 5 |
| `place` hover | `z + 0.04·n + 0.06`, lower `−0.05` | `n` = cubes already stacked; 4 cm per cube | | a cylinder or other height breaks the 0.04 |
| home pose | `[0.16, −0.06, 0.32, 0, 1.57, 0]` | out of the camera's view of the table | do not change blindly | |
| pump orientation | pitch `3.14159` | pump pointing down | | |
| bin poses A–D | e.g. A `[0.13, 0.17, 0.15, 0, 3.14, 0]`; B has `rz = 1.57` (tube out of the way); C has `ry = 2.4` (reachability) | measured positions 15 cm above the bins | move 1–2 cm | check reachability in RViz first |
| goal tolerance | position 1 mm sphere; orientation 0.01 rad per axis | exact grasp pose | 3–5 mm, 0.05 rad | the tight values make planning fail near the edges; looser = more success, less exact |
| planning | 10 attempts, 5 s, velocity/acceleration scaling 1.0 | speed | 0.3–0.5 scaling | 1.0 × the joint limit of 2.0 rad/s is fast (default scaling in `joint_limits.yaml` is 0.5) |
| Cartesian `max_step` | 0.01 m | interpolation resolution of straight lines | 0.005 | finer = more waypoints, smoother |
| IK solver | KDL, timeout 5 ms, resolution 0.005 | `kinematics.yaml` | timeout 0.05 | the 5 ms timeout is a likely cause of planning failures **[check]** |
| `cubes_stacked` | 2 | the red cube is the base | | hard-coded stack logic |

### 8.4 Lab 9 controller (`controller.py`)
| Value | Now | Why | Effect / watch for |
|---|---|---|---|
| `/joint_states` timer | 0.05 s (20 Hz) | MoveIt needs the current state at planning start | slower: stale start state |
| speed per point | `int(100·max|velocity|)` | scale MoveIt's speed to the 0–100 API | see section 0 item 7 |
| waypoint sleep | `time_from_start` difference, skipped if ≤ 0.01 s | follow MoveIt's timing | open loop |
| pump | GPIO 20 LOW = on, HIGH = off | active-low driver | section 0 item 5 (pin 21) |

---

## 9. Experiments, safest first

| # | Experiment | Needs | Measure |
|---|---|---|---|
| 9.1 | Tune the HSV thresholds with the mouse overlay on a saved frame; compare `hsv_calibrator.py` output with the fixed ranges | no robot | masks before/after, false and missed detections |
| 9.2 | Change the morphology kernel 3 → 7 → 11 on frames with a cable or a reflection (`publish_test_image.py` or real frames) | no robot | whether the cube stays one blob; centre shift in px |
| 9.3 | Read the service answers for 5 known positions (ruler) before and after your calibration | camera, `vision` | position error in mm (mean, max) |
| 9.4 | Same cube, two lightings | camera | which colours disappear; threshold margins |
| 9.5 | In RViz (`demo.launch.py`): vary hover height, tolerances, scaling factors | simulation | planning success rate, time per move |
| 9.6 | Simulation: observe what the controller would receive: log `speed` values | simulation | whether speeds exceed 100 (section 0 item 7) |
| 9.7 | Real robot, one cube near the centre, bin A: record one full cycle with a stopwatch; then change **one** of speed/hover/tolerance | robot [MOVES] | cycle time, success, grasp offset in mm |
| 9.8 | Pump test: compare Lab 8's `pump_on` (both pins LOW) with the Lab 9 topic (pin 20 only) holding the same cube | pump | hold time, release |
| 9.9 | Task E: ask for an absent colour, two same-colour objects | vision + service | `found` flag, ids, which match is chosen |

Keep a table: value, old, new, result, photo or log. The interview asks why a value is what it is.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `brain` stays at "Waiting for ... service/server" | a node is not running, or other domain id | the four things it waits for: Vision (`/cube_coordinates`), MoveIt (`move_action`, `/compute_cartesian_path`), Controller (`/arm_group_controller/follow_joint_trajectory`). `ros2 service list`, `ros2 action list`, check `ROS_DOMAIN_ID`. |
| `ros2 topic list` shows nothing from the other machine | domain id differs / multicast blocked | section 4.3 |
| Vision window does not open / `cannot connect to display` | no display (SSH, tmux) | run Vision on the machine with the screen |
| `AttributeError: module 'numpy' has no attribute 'int0'` | NumPy 2 in the Python that runs `vision` | use NumPy < 2 (ROS Jazzy ships 1.26) or replace `np.int0(box)` by `box.astype(int)` |
| `.../camera/image` stays empty | wrong device index, camera in use, no camera | `v4l2-ctl --list-devices`, `-p num:=<n>`, or `publish_test_image.py` |
| Coordinates `[1,1,1,1,1,1]` | colour not detected (or stale-free after Task B) | look at the window: is the cube outlined? thresholds, lighting |
| Planning fails ("Trajectory execution failed with error code ...") | unreachable pose, 1 mm tolerance, 5 ms IK timeout, collision objects in the way | RViz: is the goal reachable? loosen the tolerance; clear stale collision objects (restart `brain`) |
| `AttributeError ... error_code.val` after a failed Cartesian path | bug in `send_cartesian_path` (the result is an int) | known issue 10 below; not your mistake |
| Arm ends above or in the cube | z convention / camera offset | Task A step 5; measure with a ruler |
| `could not open port /dev/serial0` | another process holds it | `fuser -v /dev/serial0`; stop it |
| Pi hangs, SSH times out | out of memory | `free -h`; stop Jupyter or MoveIt there; gameplan §9 rule 7 |

---

## 11. Problems found in the code (for the report, "limitations")

`vision.py`: persistent `detected_cubes` (stale detections), constants for an old camera pose, `z = 0.01`, `np.int0`, blue S/V ≥ 200 vs 100 in the README, red hue up to 200, `cv2.namedWindow` in the constructor, one object per colour.
`brain.py`: recursive menus, `rejoice()` after each run, `error_code.val` on an `int`, `"world"` frame in the Cartesian request, tight goal tolerances, box centre at 0.01, id = colour, hard-coded `cubes_stacked = 2`.
`controller.py`: open-loop replay, speed mapping (up to 200 vs 0–100), only pin 20 for the pump, no cancel handler.
`motion_node.py` (Lab 8): moves on start, stop key disabled by default, hardcoded `/home/tejas/...` paths in the vision node.
Details and the improved versions: `Lab9_PickAndPlace_MoveIt_solution.ipynb` (Part 0, Tasks A–E) and `Lab8_PickAndPlace_solution.ipynb` (Task 24).
