# Lab 9 runbook (Lab PC + Pi)

Plain step list to follow from a text editor. Background, safety details and values to tune:
`solutions/Lab8_Lab9_run_guide.md`. Written 2026-10-01.

Machines:
- **Lab PC** `CoRobot2`, 129.217.130.101: camera, vision, MoveIt, brain, RViz.
- **Pi** `cobot-pi1`, 129.217.130.85, login `ssh cobot`: only the controller (robot serial + pump GPIO).
- Both on branch `myCobot-lab`. ROS domain **47** (change it in both `~/rosenv9.sh` if the TAs give another number).

Paste tip: if a pasted line starts with `^[[200~`, delete it and paste again with **Ctrl+Shift+V**.

---

## Part A: one-time setup

Status 2026-10-01: A1–A6 done; **A7 not yet run**.

### A1. Lab PC: install (sudo) [done]
```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-configs-utils ros-jazzy-moveit-msgs ros-jazzy-control-msgs \
     ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-controller-manager \
     ros-jazzy-joint-trajectory-controller ros-jazzy-joint-state-publisher-gui ros-jazzy-xacro v4l-utils tmux
```
OK = no `E:` lines. (`ros-jazzy-warehouse-ros-mongo` does not exist for Jazzy: leave it out.)

### A2. Lab PC: build [done]
New terminal, venv **not** active (the build must use the system Python):
```bash
deactivate 2>/dev/null; source /opt/ros/jazzy/setup.bash
cd ~/mycobot-project/pp_moveit_ws
colcon build --symlink-install --packages-up-to mycobot_brain mycobot_vision mycobot_280_moveit2 mycobot_280pi
source install/setup.bash && ros2 pkg list | grep mycobot
```
OK = 6 packages: `mycobot_280_moveit2 mycobot_280pi mycobot_brain mycobot_description mycobot_interfaces mycobot_vision`.

### A3. Lab PC: camera index [done: /dev/video0 → index 0]
```bash
v4l2-ctl --list-devices
```
`Logitech Webcam C930e` → first `/dev/videoN` → use `num:=N` in B4.

### A4. Pi: build the controller [done]
```bash
ssh cobot
source /opt/ros/jazzy/setup.bash
cd ~/mycobot-project/pp_moveit_ws
colcon build --symlink-install --parallel-workers 1 --packages-select mycobot_controller
```
OK = `Summary: 1 package finished`.

### A5. Firewalls (sudo, both machines) [done: UDP verified both ways]
```bash
# Lab PC
sudo ufw allow from 129.217.130.85 comment 'cobot-pi1 ROS 2'
# Pi
sudo ufw allow from 129.217.130.101 comment 'CoRobot2 ROS 2'
```
Check: `sudo ufw status` shows an ALLOW line for the other machine.
Undo: `sudo ufw delete allow from <ip>`. If an IP changes (`hostname -I`), redo the rule.

### A6. `~/rosenv9.sh` on both machines [done]
One line, safe to paste:
```bash
printf '%s\n' 'source /opt/ros/jazzy/setup.bash' 'source ~/mycobot-project/pp_moveit_ws/install/setup.bash' 'export ROS_DOMAIN_ID=47' 'unset ROS_LOCALHOST_ONLY ROS_AUTOMATIC_DISCOVERY_RANGE' > ~/rosenv9.sh && source ~/rosenv9.sh && ros2 daemon stop; echo "domain=$ROS_DOMAIN_ID"
```
OK = `domain=47`. **Every Lab 9 terminal starts with `source ~/rosenv9.sh`.**

### A7. Network test (no motion) [TODO]
1. Lab PC: `source ~/rosenv9.sh && ros2 multicast receive`   (waits)
2. Pi:     `source ~/rosenv9.sh && ros2 multicast send`
   OK = Lab PC prints `Received from 129.217.130.85:... 'Hello World!'`
3. Pi:     `ros2 topic pub /chatter std_msgs/msg/String "{data: hi}" -r 1`
   Lab PC: `ros2 topic echo /chatter`
   OK = `data: hi` every second. Ctrl+C both.

If A7 fails: stop. Check A5 (`sudo ufw status` on both) and `domain=47` on both.
Still failing → the lab network blocks multicast: ask the TAs.

---

## Part B: every session

### B0. Simulation first (Lab PC only, **controller OFF**)
```bash
source ~/rosenv9.sh
ros2 launch mycobot_brain brain_simulation.launch.py
```
Opens 4 tabs (Brain, MoveIt + RViz, camera, Vision). Brain tab: `2` (sort) → a colour → bin `A`; watch RViz.
The real controller must **not** run at the same time. Close all tabs before B1.

### B1. Pi: controller (no motion yet)
```bash
ssh cobot
tmux new -s ctl                 # or: tmux attach -t ctl
source ~/rosenv9.sh
ros2 run mycobot_controller controller
```
OK = `Joint state publisher ready!`, `Pump ready!`, `FJT action server ready!`, `Current coordinates: [...]`.
Detach: Ctrl+B, then D.
Port busy? `fuser -v /dev/serial0` → close the notebook kernel / stop `mycobot_control` first.

### B2. Lab PC terminal 1: robot data over the network
```bash
source ~/rosenv9.sh && ros2 topic echo /joint_states --once
```
OK = six joint values. Nothing → back to A7.

### B3. Lab PC terminal 2: MoveIt
```bash
source ~/rosenv9.sh && ros2 launch mycobot_280_moveit2 move_group.launch.py
```
OK = `You can start planning now!`

### B4. Lab PC terminal 3: camera
```bash
source ~/rosenv9.sh && ros2 run mycobot_280pi opencv_camera --ros-args -p num:=0
```
Check (another terminal): `ros2 topic hz camera/image` ≈ 10 Hz.

### B5. Lab PC terminal 4: vision + check (no motion)
```bash
source ~/rosenv9.sh && ros2 run mycobot_vision vision
```
OK = window with rectangles on the cubes + `Cube coordinate service ready!`. Then:
```bash
source ~/rosenv9.sh && ros2 service call /cube_coordinates mycobot_interfaces/srv/GetCubeCoords "{color: red}"
```
OK = x ≈ 0.08…0.23, y ≈ −0.075…0.075. `[1.0, 1.0, ...]` = colour not detected.

### B6. Lab PC terminal 5: brain — MOVES, start it LAST
Workspace clear, one person at the power switch.
```bash
source ~/rosenv9.sh && ros2 run mycobot_brain brain
```
- Waits for 4 servers, then **moves the arm to home by itself**, then shows the menu.
- First run: `2` (sort) → one cube near the centre → bin `A`.
- After **every** run the arm goes **straight up (all zeros) and back** ("rejoice"): keep the space above it clear.

---

## Part C: stop
1. Brain menu: `exit`, then Ctrl+C (switches the pump off).
2. Ctrl+C vision, camera, MoveIt (terminals 2–4).
3. Pi: `tmux attach -t ctl` → Ctrl+C → `exit`.
4. Pi: commit + `git push` your changes.

**Emergency stop = the robot's power switch.** Ctrl+C in brain does not stop a trajectory already sent.

---

## Part D: first pick and place with the camera (Lab 9 Part 0)

No code or notebook edits are needed: this runs the **unchanged course code**. `solutions/Lab9_…ipynb` is only a
reference for Tasks A–E (synthetic data); nothing at runtime uses it.

**The one real risk:** `vision.py` `send_cube_coords()` (lines 44–49) maps pixels to robot coordinates with fixed
numbers measured for the **old** camera pose (the PDF says the camera moved):
```python
rx = 0.08   + (cy - 55)  / 280.0 * 0.15     # pixel row    → robot x (m)
ry = -0.075 + (cx - 185) / 280.0 * 0.15     # pixel column → robot y (m)
z  = 0.01                                    # fixed height
```
So check the accuracy **before** `brain` (the first thing that moves the arm).

### D1. Start everything except brain
Part B steps B1–B5 (controller on the Pi → `/joint_states` check → MoveIt → camera `num:=0` → vision). No motion.

### D2. Image size (vision assumes 640×480)
```bash
source ~/rosenv9.sh
ros2 topic echo /camera/image --once --field width;  ros2 topic echo /camera/image --once --field height
```
OK = `640` and `480`. Anything else → the pixel constants cannot be right: stop.

### D3. Accuracy check (no motion, ~10 min)
Robot base frame: origin = centre of the base, **x forward** (away from the robot, into the camera view), **y left**.
Put **one red cube** at each position (ruler from the base centre) and ask vision:
```bash
ros2 service call /cube_coordinates mycobot_interfaces/srv/GetCubeCoords "{color: red}"
```
| Placed at (x, y) m | Returned (x, y) | Error |
|---|---|---|
| (0.15, 0.00) | | |
| (0.10, −0.05) | | |
| (0.20, 0.05) | | |

- Vision window: the red cube must have a **rectangle**. `[1.0, 1.0, ...]` = not detected → fix lighting/thresholds first.
- Errors **≤ ~1 cm** → D4.
- Larger → stop. Either (a) **Task A** (ArUco calibration): the real fix, and one of your two tasks; or (b) a
  **temporary workaround** for a first run: re-fit the 4 numbers in lines 44–47 from the measured points. Mark it as a
  workaround in the report (it breaks again if the camera moves).

### D4. First run (Part B step B6) — MOVES
- One person at the power switch; workspace clear; **space above the arm clear** (after every run the arm goes
  straight up and back: "rejoice").
- Start `brain` → it moves to home by itself → menu.
- Menu `2` (sort) → `r` → wait until the cube is gripped → bin `A`. Then `exit`.
- Only when that worked: `1` (stack), cubes placed as the PDF describes.

### D5. Record for the Part 0 report (PDF deliverable)
Per run: initial cube positions, menu choices, bin, outcome (success / missed / dropped). Plus:
- the **data flow** of one pick: camera → `camera/image` → vision (HSV, pixel → robot) → `/cube_coordinates` → brain →
  MoveIt (`/move_action`, `/compute_cartesian_path`) → controller → arm; `/pump_controller` → pump;
- **at least 2 limitations** you observed (likely: fixed pixel mapping, fixed z = 0.01, one object per colour,
  lighting sensitivity, open-loop trajectory replay).
Compare with the Part 0 checklist in `solutions/Lab9_…ipynb` **after** writing your own.

### Known surprises
- **Blue needs S and V ≥ 200** → often missed in normal light. Start with red.
- Weak suction: the Lab 9 controller switches only pump pin 20 (not 21).
- Ctrl+C in brain does not stop a move already sent. The power switch does.

---

## Quick fixes
| Symptom | Fix |
|---|---|
| `source: command not found` in a script | paste artefact `^[[200~` in the file: recreate it with the A6 one-liner |
| brain waits forever for a server | a node is missing or a different domain: `ros2 node list`, `echo $ROS_DOMAIN_ID` on both |
| `/joint_states` not seen on the Lab PC | A7; controller running? (`tmux attach -t ctl`) |
| camera topic empty | wrong index: A3, then `num:=N` |
| vision window doesn't open | run vision on the Lab PC (needs its display), not over SSH |
| `could not open port /dev/serial0` | `fuser -v /dev/serial0` → stop that process |
| Pi slow / SSH timeouts | `free -h` on the Pi; nothing but the controller should run there |
