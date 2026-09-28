# CoRobot Lab: setup + game plan
Written 2026-09-27 with Claude Code. Course starts **Mon 28.09.2026**, Mo–Fr 9:00–17:00, IRF Mobile Robot Lab Area.
Moodle: https://moodle.tu-dortmund.de/course/view.php?id=59336 · TAs: Shreyas Desikan, Kavish Punitbhai Gajjar

---

## Part A: ROS 2 Jazzy install (course PDF vs official docs)

State on 2026-09-27: Ubuntu 24.04.5, locale `en_US.UTF-8`, `universe` enabled, `noble-updates` and
`noble-backports` in apt sources. **No ROS yet** (no repo, no `/opt/ros`). `.bashrc` line 120 = old commented Humble line.
`~/venvs/mycobot` exists (made from the PDF, `include-system-site-packages = false`, colcon/rosdep pip-installed).

**Update 2026-09-28: A.1 + A.2 done and verified.** ROS Jazzy installed via `ros2-apt-source`, rosdep initialised,
line 120 sources Jazzy, and the venv sees system packages (`import rclpy, roboticstoolbox, spatialmath` works).
**Next: A.3** (build `ros2_ws`).

| Step | Course PDF (`SystemSetup_Ubuntu_ROS2.pdf`) | Official (docs.ros.org Jazzy) | Do |
|---|---|---|---|
| Locale, universe | same | same | skip, already done |
| Repo + key | manual `ros.key` + `ros2.list` | `ros2-apt-source` .deb (key auto-renews) | **official**; never both (apt error "Conflicting values set for option Signed-By") |
| Dev tools | `python3-rosdep python3-colcon-common-extensions` | `ros-dev-tools` (colcon, rosdep, vcstool, …) | `ros-dev-tools` |
| Install | `ros-jazzy-desktop` | same | same |
| Sourcing | appends to `.bashrc` | `source /opt/ros/jazzy/setup.bash` | **replace line 120** (no duplicate) |
| rosdep init/update | yes | in tutorials | do it |
| venv | plain venv | "use the system interpreter" | **system-site-packages** (see A.2) |

### A.1 Install (run in your own terminal; sudo)
```bash
sudo apt update && sudo apt upgrade -y

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
echo $ROS_APT_SOURCE_VERSION        # must print a version (1.3.0 on 2026-09-27), not an empty line
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

sudo apt update && sudo apt upgrade -y
sudo apt install ros-jazzy-desktop ros-dev-tools

sed -i '120s|^# source /opt/ros/humble/setup.bash.*|source /opt/ros/jazzy/setup.bash|' ~/.bashrc
grep -n "opt/ros" ~/.bashrc           # expect: 120:source /opt/ros/jazzy/setup.bash
source ~/.bashrc

sudo rosdep init
rosdep update

# test: 2 terminals
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_py listener       # should print "I heard: ..."
```

### A.2 Fix the existing venv (no need to recreate it)
A plain venv can't see apt's Python modules (`em`, `lark`, `catkin_pkg`, ROS's numpy), so building message
packages like `mycobot_msgs`/`mycobot_interfaces` inside it tends to fail with `No module named 'em'`.
One line switches it to see system packages (pip-installed packages in the venv still win):
```bash
sed -i 's/^include-system-site-packages = false/include-system-site-packages = true/' ~/venvs/mycobot/pyvenv.cfg
source ~/venvs/mycobot/bin/activate
python -m pip install jupyterlab roboticstoolbox-python spatialmath-python sympy pyserial pymycobot "numpy<2"
```
- Keep the pip `colcon-common-extensions` in the venv: nodes built with it run on the venv's Python, so they see
  venv packages (that's why the course readme builds inside the venv).
- `numpy<2` keeps ROS's own compiled Python parts (e.g. `cv_bridge`, built against numpy 1.26) working.
  The YOLO lab (Lab 8) uses numpy 2.x → it gets its **own** venv (`yolovenv`), exactly as its readme says.

### A.3 Workspaces (unzipped on 2026-09-27; build them once ROS is installed)
Separate workspaces, because `mycobot_description` and `mycobot_controller` exist in more than one zip
(duplicate package names break `colcon build`). Code is unchanged from the zips.

| Workspace | From | Packages | For |
|---|---|---|---|
| `~/TUD/cobots/ros2_ws` | `FK_to_TP Control.zip` | `mycobot_control`, `mycobot_description` | Labs 2–7 (name matches the codebase's own `/home/mycobot/ros2_ws`) |
| `~/TUD/cobots/pp_moveit_ws` | `Pick and Place Packages.zip` | `mycobot_280_moveit2`, `mycobot_280pi`, `mycobot_brain`, `mycobot_controller`, `mycobot_description`, `mycobot_interfaces`, `mycobot_vision` | Lab 9 |
| `~/TUD/cobots/pp_yolo_ws` | `Lab 09 PP.zip` | `vision`, `mycobot_msgs`, `mycobot_motion_v1` (+ `weights/`, `Vision_requirements/` next to `src/`) | Lab 8 |

`Pick and Place Control.zip` was **not** extracted: its `mycobot_controller` code is identical to the one in the
Packages zip (only README formatting differs). The two `mycobot_description` copies are byte-identical.

```bash
# Labs 2–7 (do this tonight, after A.1 + A.2)
cd ~/TUD/cobots/ros2_ws && rosdep install --from-paths src --ignore-src -r -y
source ~/venvs/mycobot/bin/activate && colcon build --symlink-install

# Lab 9, when you get there (rosdep pulls MoveIt 2)
cd ~/TUD/cobots/pp_moveit_ws && rosdep install --from-paths src --ignore-src -r -y
source ~/venvs/mycobot/bin/activate && colcon build --symlink-install

# Lab 8, only if required: own venv per ~/TUD/cobots/pp_yolo_ws/Vision_requirements/Vision_Setup_readme.txt
python3 -m venv --system-site-packages ~/venvs/yolovenv && source ~/venvs/yolovenv/bin/activate
python -m pip install --no-cache-dir -r ~/TUD/cobots/pp_yolo_ws/Vision_requirements/requirements.txt
cd ~/TUD/cobots/pp_yolo_ws && colcon build --symlink-install
```
`rosdep -r` continues past keys that can't resolve on a laptop. Expected ones: `gazebo_ros_control` (Gazebo Classic,
not in Jazzy), `python3-rpi.gpio` (only needed on the robot's Pi), `python3-pymycobot` (pip-installed above).

**Hardcoded paths in the code** (left as they are; they point at the robot's Pi or earlier developers' machines):
- `mycobot_control.launch.py`: `port /dev/serial0`, `urdf_path /home/mycobot/ros2_ws/src/mycobot_280_gazebo.urdf` → the
  controller runs **on the robot's Pi**, not on the laptop.
- `scripts/ik_debug.py`, `scripts/fk_tool_calib.py`: URDF `/home/harshit/...` (ik_debug takes `--urdf`).
- Lab 8 `vision_node.py`: weights `/home/tejas/YOLO/.../best.pt` (yours: `~/TUD/cobots/pp_yolo_ws/weights/best.pt`),
  `CALIB_FILE /home/tejas/z_scale_calibration.json`, camera `/dev/video2`. Adjust only when you actually run it.

**Missing file: `mycobot_280_gazebo.urdf`.** Labs 2–6 load it from the notebooks' folder (`~/TUD/cobots/`), and so does RViz2 in Lab 2.
It's in none of the zips ("tutor distribution"). Get it from Moodle/TAs → put it in `~/TUD/cobots/`.
Until then, `~/TUD/cobots/ros2_ws/src/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf` has the same
`g_base` → `joint6_flange` chain and can be used to try things out, but not for results you hand in.

### A.4 Start Jupyter for the labs (every time)
```bash
source ~/venvs/mycobot/bin/activate
source ~/TUD/cobots/ros2_ws/install/setup.bash       # ROS itself is already sourced by .bashrc
cd ~/TUD/cobots && jupyter lab
```
Smoke test in a notebook cell: `import rclpy, roboticstoolbox as rtb, spatialmath; print("ok")`.

---

## Part B: Game plan

### The course in one paragraph
Groups of 2–3, 9 labs on the **myCobot 280 Pi** (6-DOF, Raspberry Pi 4 inside, suction pump, top camera).
You upload solution code; **the grade comes from a final interview** where you explain your code, the robot
behaviour and the theory. LLMs are allowed for help, but you must understand everything you submit, and
you can't use them in the interview. So: **understanding > finishing.**

### The 9 labs (template notebooks are in this folder)
| # | Lab (PDF) | Tasks | Where | What it's really about |
|---|---|---|---|---|
| 1 | Spatial Transformations | 33 | laptop, pure Python | rotations, homogeneous T, RPY/Euler/axis-angle, quaternions, SLERP |
| 2 | Forward Kinematics | 29 | laptop + ROS/RViz2 | DH table of myCobot, manual vs URDF model, publish joints to ROS |
| 3 | Inverse Kinematics | 18 | laptop (last task: robot) | numerical IK: rtb solver, `least_squares`, damped least squares, seeds |
| 4 | Differential Kinematics | 20 | laptop (last 2: robot) | Jacobian, singularities (SVD), manipulability, resolved-rate control |
| 5 | TCP Calibration | 18 | robot measurements | flange→TCP offset, SVD mean rotation, residuals |
| 6 | Trajectory Planning | 19 | laptop | trapezoid/triangle profiles, synchronised joints. **Moodle quiz before the lab** |
| 7 | Serial Communication | 29 | **real robot** | frames `FE FE LEN CMD … FA`, read/send angles, stop/resume, position vs velocity mode |
| 8 | Pick & Place v1 (`Pick_And_Place.pdf`, Apr) | 28 | robot | YOLO + solvePnP + pymycobot + GPIO pump (`Lab 09 PP.zip`) |
| 9 | Pick & Place v2 (`Pick_And_Place-2.pdf`, Sep 23) | explore + **2 of 5** extensions | robot + MoveIt | Brain/Vision/MoveIt/Controller nodes, HSV, ArUco |

Extensions for Lab 9 (choose two): ① ArUco camera calibration ② robust HSV masking ③ interactive HSV threshold
calibration ④ shape detection (cube vs cylinder) ⑤ extend object interface (select by color + shape).
- **Low-risk pair:** ② + ③. Both are pure OpenCV and can be developed at home on saved camera images.
- **Best for the interview:** ① + ②. ① reuses the transform maths from Labs 1–2.

### Phases
**Phase 0 – tonight (Sun 27.09), ~1–2 h:** Part A. Done when the talker/listener test works, `~/TUD/cobots/ros2_ws` builds,
and the Jupyter smoke test prints `ok`. If something fails, don't spend the night on it. Bring the error to the TAs tomorrow.

**Phase 1 – day 1:** kick-off, safety briefing, form your group. Ask the TAs:
1. Is Lab 8 (YOLO, April PDF) still required, or only Lab 9 (MoveIt, Sep 23 PDF)? The 25.09 intro slides only show Lab 9.
2. Do the robot notebooks (Labs 7, 8) run **on the robot's Pi**? `serial_iface.py` uses `/dev/serial0` and the launch
   file has `/home/mycobot/...` paths, so they probably do. How does the laptop reach the Pi (network, SSH, Jupyter)?
3. Which **`ROS_DOMAIN_ID`** should your group use? Several robots on one network will otherwise see each other's topics.
4. Deadlines for uploads + interview date/format; is this a 2-week block?
5. Where do you get **`mycobot_280_gazebo.urdf`** (and the optional `pointcloud.mat` for Lab 1)? Not in any zip.

**Phase 2 – Labs 1–4 (maths core, mostly laptop):** most of the interview theory comes from these. Pre-read Siciliano
ch. 2.1–2.7 (and the kinematics chapters) as the PDFs recommend. Finish these fast. They don't need a robot, so do them
at home and save lab time for the robot.

**Phase 3 – Labs 5–7 (robot):** do all offline cells before your robot slot. In the lab, only measure/run, save data and
plots. Always small motions first, stop command ready, compare commanded vs measured.

**Phase 4 – Lab 9 (+8 if required):** run the existing system first (sorting/stacking menu), write the data-flow
report, then pick the 2 extensions on day 1 of this phase and split them in the group.

### Routine for every lab (this is the interview prep)
1. **Before:** read the PDF, answer its *Short Questions* in your own words (they're basically interview questions).
2. **During:** notebook top to bottom. For LLM-generated code: you must be able to explain every line.
3. **After:** upload code + write a ½-page "interview card": goal, key formula, 1 result plot, 1 pitfall you hit.
4. Group repo: **github.com/manojkumar-org/mycobot-project** (keep it private; this folder is its working copy, set up 2026-09-28;
   large course files are git-ignored, see README.md). Never edit `originals/`. Rotate who drives so everyone
   can explain everything.

### Where everything is
```
~/TUD/cobots/                    (layout changed 2026-09-27: everything for the course in one place)
├── GAME-PLAN.md                 (private: .git/info/exclude, never pushed)
├── *Template.ipynb              WORK HERE: the 8 lab notebooks
├── helperFunctions.py           used by IK / Diff / TCP notebooks
├── serial_iface.py              used by Lab 7 (copy of ros2_ws/src/mycobot_control/mycobot_control/serial_iface.py)
│                                (+ mycobot_280_gazebo.urdf here once you have it)
├── ros2_ws/                     Labs 2–7 ROS code   (from FK_to_TP Control.zip)
├── pp_moveit_ws/                Lab 9 ROS code      (from Pick and Place Packages.zip)
├── pp_yolo_ws/                  Lab 8 ROS code      (from Lab 09 PP.zip, + weights/, Vision_requirements/)
├── pdfs/                        the 11 PDFs (intro, system setup, 9 lab texts); private, not in git
└── originals/                   as downloaded, don't edit: the 4 zips + untouched template copies (backup); private, not in git
~/venvs/mycobot   Python env for everything (Lab 8 YOLO: ~/venvs/yolovenv)
```
Why 3 separate workspaces and not one: `mycobot_description` and `mycobot_controller` exist in more than one zip,
and duplicate package names break `colcon build`. `Pick and Place Control.zip` isn't extracted (it duplicates the
Packages zip's controller).
Notebook ↔ lab: SpatialTransformations = 1, ForwardKinematics = 2, InverseKinematics = 3, DifferentialKinematics = 4,
TCPCalibration = 5, TrajectoryPlanning = 6, SerialCommunicationRobotControl = 7, PickAndPlace = 8.
Lab 9 has no notebook: you work in `~/TUD/cobots/pp_moveit_ws` (`mycobot_brain/brain.py`, `mycobot_vision`).
