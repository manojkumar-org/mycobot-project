# Lab 9 on the real robot: course ROS pipeline + the setup that worked (2026-10-05)

The course system (camera → vision → brain → MoveIt → controller) with today's working values from
[`solutions/lab9_simple/`](../lab9_simple/) (marker calibration, 35 mm objects, heights, bins, pump valve).
Original `vision` / `brain` stay unchanged for the Part 0 baseline. The old step-by-step guide for Tasks A–C is in
[`old_tasks_ABC/`](old_tasks_ABC/).

**Status:** built on the Lab PC; detection tested on the 10-02 reference frame; brain tested end to end in MoveIt
simulation (fake controller): blue cylinder and yellow cube picked and dropped into their bins. **Not yet run on the robot.**

```
Lab PC (ROS_DOMAIN_ID 47)                                              Pi cobot-pi1
opencv_camera ──camera/image──▶ vision_lab9 ── /get_object ──▶ brain_lab9 ── /pump_controller ──▶ controller
  /dev/video0                   markers + HSV + shape          menu, scene     ── follow_joint_trajectory ──▶  serial ttyAMA0
                                (/cube_coordinates: original)      │                                         GPIO 20 pump, 21 valve
                                                                   └─▶ move_group (MoveIt) ◀── /joint_states 20 Hz ──┘
```

| File | New / changed | What |
|---|---|---|
| `lab9.yaml` (this folder) | new | every value: markers, plate height, sizes, HSV, shape thresholds, heights, bins |
| `pp_moveit_ws/src/mycobot_interfaces/srv/GetObject.srv` | new | request `color`, `shape`, `id` → `found`, `id`, `shape`, `coords`, `height`, `matches` |
| `pp_moveit_ws/src/mycobot_vision/mycobot_vision/vision_lab9.py` | new | calibration, per-colour HSV masks, shape features, object list, `/get_object`, `/cube_coordinates` |
| `pp_moveit_ws/src/mycobot_brain/mycobot_brain/brain_lab9.py` | new (from `brain.py`) | object interface, BOX/CYLINDER scene objects, heights + bins from `lab9.yaml`, menu loop, auto sort |
| `pp_moveit_ws/src/mycobot_brain/launch/lab9_real.launch.py` | new | tabs: MoveIt, camera, vision_lab9 (brain is started by hand, last) |
| `pp_moveit_ws/src/mycobot_controller/mycobot_controller/controller.py` | changed | pump on/off also switches valve pin 21 (as in Lab 8), so objects are released |
| `setup.py` of vision and brain, `mycobot_interfaces/CMakeLists.txt` | changed | entry points `vision_lab9`, `brain_lab9`; `GetObject.srv` |

## 1. Lab tasks covered (2 of 5)

| PDF task | Where | Done |
|---|---|---|
| **Object shape detection** | `vision_lab9.py` `detect()`, `classify()` | HSV mask per colour, opening + closing, size filter (30–75 mm); features: area, perimeter, centre (moments), `minAreaRect`, circularity `C = 4πA/P²`, `approxPolyDP` vertices, fill = A / enclosing-circle area; label `cube` / `cylinder` / `unknown`; several objects per colour; a new list every frame (removed objects disappear, nothing older than 1 s is returned); contours + labels in the window |
| **Extension of the object interface** | `GetObject.srv`, `brain_lab9.py` | request by colour + shape (+ id), explicit `found`, unique id (`red_cube_1`), all `matches`; `get_object()`, `spawn_object()` (BOX / CYLINDER, 35 mm), ids used for add / attach / detach / remove; menu asks colour + shape and lists matches; menu is a loop, not recursive calls |
| Calibration (needed, **not** graded Task A) | `PlaneMap` in `vision_lab9.py` | 2 marker centres (robot-measured) → scale, rotation, shift on the plate + correction for the object height. Task A asks for K + `solvePnP` with all 8 corners; the PDF says 2 centres are not enough for a full pose. Works here because the camera looks straight down (checked: workspace box on the plate within ~5 px). |

Shape rule (`lab9.yaml` → `shape`): cylinder if fill ≥ 0.75 and C ≥ 0.75; cube if fill ≤ 0.72, C ≤ 0.85 and 4–6 vertices;
else `unknown`. Fill is the main criterion (a square fills 64 % of its enclosing circle, a circle 100 %; it separated cubes
and cylinders live on 10-05). Circularity alone is weak: pixel noise lowers it (10-02 frame: cylinder C 0.82).

## 2. Values (`lab9.yaml`)

Copied from `lab9_simple/config.py` (mm → m). Change values in **both** files until `lab9_simple` is retired.

| Value | Now | How to get it |
|---|---|---|
| `markers.centers` | id 1 (0.135, −0.060), id 2 (0.255, 0.060) | ruler from the robot centre to each marker centre (plate moved +45 mm on 10-05) |
| `objects.surface_z_m` | 0.012 | lowered until the suction made contact (pick worked at flange z 115 mm) |
| `objects.cylinder_h_m` | 0.035 | **MEASURE** (assumed = cube) |
| `camera.height_m` | 0.47 | **MEASURE** lens → plate (estimate) |
| `robot.bins` | red (0.065, 0.170), yellow (0.200, 0.170), blue (0.185, 0.170) | check that each bin circle is over its bin |
| `robot.drop_tip_z_m` | 0.100 | clears a cube already in the bin by ~25 mm |

Frames: `g_base` (MoveIt) = pymycobot base frame. MoveIt's `pump_head` is flange + 40 mm, the real nozzle tip flange + 68 mm,
so the brain sends `pump_head z = object top + 0.028` for contact (= the flange z 115 mm that worked with pymycobot).

## 3. One-time setup

```bash
# Lab PC (done 10-05; repeat after pulling changes to these packages)
cd ~/mycobot-project/pp_moveit_ws && source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select mycobot_interfaces mycobot_vision mycobot_brain
```
```bash
# [Pi] get controller.py with the valve fix (token needed after a reboot)
cd ~/mycobot-project
git checkout -- solutions/lab9_simple          # copies sent by scp; identical to the commit
git pull
cd pp_moveit_ws && source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --parallel-workers 1 --packages-select mycobot_controller
```
Both machines: `source ~/rosenv9.sh` in every terminal (ROS Jazzy + `pp_moveit_ws/install` + `ROS_DOMAIN_ID=47`).

## 4. Run (order matters)

Only one program may use the robot: no Jupyter kernel and no `robot_pi.py` (`lab9_simple`) while the controller runs.

| # | Where | Command | Check |
|---|---|---|---|
| 1 | [Pi] terminal 1 | `source ~/rosenv9.sh && ros2 run mycobot_controller controller` | `Pump ready!`, `FJT action server ready!`, current coordinates printed |
| 2 | Lab PC | `source ~/rosenv9.sh && ros2 topic hz /joint_states` | ~20 Hz (network + controller OK); Ctrl+C |
| 3 | Lab PC (desktop) | `source ~/rosenv9.sh && ros2 launch mycobot_brain lab9_real.launch.py` | 3 tabs: MoveIt (`You can start planning now!`), Camera, Vision (`calibrated: … 1.0 mm/px, rotation ~89 deg`) |
| 4 | Lab PC | look at the `vision_lab9` window | yellow box on the plate, magenta circle on the robot base, each object outlined + `red_cube_1 (x, y) mm` |
| 5 | Lab PC | `ros2 service call /get_object mycobot_interfaces/srv/GetObject "{color: red, shape: cube}"` | `found=True`, coords in m, `matches` |
| 6 | Lab PC, new terminal **[MOVES]** | `source ~/rosenv9.sh && ros2 run mycobot_brain brain_lab9` | arm goes home, then the menu |

Menu: `1` pick one object (colour, shape, select a match, bin; Enter = the object's own colour bin), `2` auto sort
(all objects into their colour's bin, order red → yellow → blue), `3` stack cubes (red bottom, then yellow, blue), `q` quit.
Vision window keys: `c` re-read the markers (uncover them first), `s` save raw + annotated frame to `lab9/frames/`.
Stop: `q` in the brain (pump off), Ctrl+C in the controller last.

Manual start instead of step 3 (e.g. without a desktop): `ros2 launch mycobot_280_moveit2 move_group.launch.py`,
`ros2 run mycobot_280pi opencv_camera`, `ros2 run mycobot_vision vision_lab9`, each in its own terminal.

## 5. Part 0 baseline (original system)

Same steps 1–2, then the original nodes: `ros2 launch mycobot_brain brain.launch.py` (brain, MoveIt, camera, `vision`).
Expected weaknesses to document (run guide `solutions/Lab8_Lab9_run_guide.md` §6d): `vision` finds nothing or wrong
positions with this camera (fixed pixel map of the old camera, 50–150 px size filter, blue thresholds), 40 mm box in the
scene, one object per colour. Record what you see before switching to `vision_lab9`. (The controller's valve fix applies
to both versions.)

## 6. Evaluation (deliverables)

**Shape detection**
1. Scenes: cubes and cylinders of several colours, two objects of the same colour, one cube rotated ~30°. Press `s` in each.
2. Report per scene: labels and centres from the vision log (`objects: red_cube_1 (150, 20) C 0.80 fill 0.65 v 4, …`,
   printed whenever the scene changes) against a ruler; C, fill and v (vertices) justify each label.
3. One uncertain case: e.g. a cylinder touching a cube of the same colour (merged blob → `unknown` or wrong shape).

**Object interface**
```bash
ros2 service call /get_object mycobot_interfaces/srv/GetObject "{color: red, shape: cube}"       # existing
ros2 service call /get_object mycobot_interfaces/srv/GetObject "{color: red, shape: cylinder}"   # absent -> found False
ros2 service call /get_object mycobot_interfaces/srv/GetObject "{color: blue, shape: ''}"        # several -> matches
```
Then menu `1` with two objects of the same colour (selection list) and menu `2`. Note per pick: target id, position,
success, miss in mm.

## 7. Limits and safety (what the tests showed)

- **Reach:** MoveIt plans hover + vertical descent for the plate from x ≈ 0.135 to 0.250 m (simulation, 10-05). The near
  edge (x 0.120, centre) and the far edge (x 0.265) fail planning: the brain then stops the sequence (pump off, home)
  without moving there. The pymycobot run crashed once at x 0.120: keep objects off the plate's first ~15 mm.
- **Yaw:** suction needs no yaw. MoveIt's IK fails at random for some yaws, so the brain tries 6 yaws (2 rounds) and only
  retries when nothing moved (planning errors −1, −2, −6, −31).
- The descent and lift are straight lines without collision checks against the target (touching it is the goal);
  free-space moves keep full collision checking. Velocity scaling 0.3 (course: 1.0).
- After scene changes the brain waits 0.5 s (planning earlier failed with error −2 in simulation).
- Auto sort stops after 6 picks per colour (a failed grasp cannot loop forever).
- `opencv_camera` (course) reopens the camera for every frame: ~10 Hz at best.

## 8. Troubleshooting

| Symptom | Cause → fix |
|---|---|
| brain waits for `follow_joint_trajectory` | controller not running on the Pi, or domain/firewall: step 2 |
| controller: GPIO busy / serial errors | another program holds the robot (Jupyter kernel, `robot_pi.py`): stop it |
| vision: `marker(s) [..] not visible` | uncover the markers, press `c` |
| objects not outlined / wrong shape | `hsv` / `shape` values in `lab9.yaml`; restart `vision_lab9` |
| `no plan to pick … (reach limit?)` | object outside x 0.135–0.250 m: move it closer to the plate centre |
| nozzle above / pressing into the object | `objects.surface_z_m` (±2 mm steps) |
| object not released | controller without the valve fix: `git pull` + rebuild on the Pi |
