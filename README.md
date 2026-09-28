# mycobot-project

Group repo for the **CoRobot Lab** at TU Dortmund (myCobot 280 Pi, ROS 2 Jazzy on Ubuntu 24.04).
Setup: ROS 2 Jazzy per the [official install guide](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
and the course PDF `SystemSetup_Ubuntu_ROS2.pdf` (Moodle).

## Layout
```
.
├── *Template.ipynb        lab notebooks (Labs 1–8): work here
├── helperFunctions.py     used by the IK / Diff / TCP notebooks
├── serial_iface.py        used by Lab 7
├── ros2_ws/src/           Labs 2–7 ROS 2 packages   (mycobot_control, mycobot_description)
├── pp_moveit_ws/src/      Lab 9 ROS 2 packages      (brain, vision, controller, interfaces, MoveIt 2 config, mycobot_description)
└── pp_yolo_ws/src/        Lab 8 ROS 2 packages      (vision, mycobot_msgs, mycobot_motion_v1)
```
There are 3 separate workspaces because some package names (`mycobot_description`, `mycobot_controller`) exist
in more than one course zip, and duplicate names break `colcon build`.

`mycobot_description` (robot URDFs + 3D models, 277 MB on disk) is included **complete** in both `ros2_ws` and
`pp_moveit_ws` for now, so a fresh clone builds without extra downloads. The two copies are identical, so git stores
the files only once (about 75 MB compressed). The first clone takes a while.

## Not in this repo: get them from Moodle
| What | Size | Where it goes | From |
|---|---|---|---|
| `best.pt` (YOLO weights) | 40 MB | `pp_yolo_ws/weights/` | `Lab 09 PP.zip` |
| `mycobot_280_gazebo.urdf` | — | repo root (next to the notebooks) | Moodle / TAs (not in any zip) |

## Build (after ROS 2 Jazzy is installed)
```bash
source ~/venvs/mycobot/bin/activate
cd ros2_ws && rosdep install --from-paths src --ignore-src -r -y && colcon build --symlink-install
```
`build/`, `install/` and `log/` are ignored by git.
