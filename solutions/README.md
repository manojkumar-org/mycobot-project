# Worked solutions

One notebook per lab, next to the templates in the repo root. **Use them to compare, not to copy**: solve the template yourself
first, then read the matching solution. The interview asks you to explain your own code.

Every task in a solution notebook has the same four parts:

1. **Task**: what the template asks, in a line or two.
2. **Solution**: code that runs.
3. **How it works**: each piece of syntax and each maths step, line by line.
4. **Example / check**: a small extra cell that shows the syntax on a toy case, or verifies the result.

The saved outputs come from running each notebook top to bottom (plots as static images). Run them yourself for interactive plots
(`%matplotlib widget`). The PDFs' short questions are answered at the end of the notebooks that have them (Labs 5–8).

| Notebook | Template / PDF | Runs on | Status |
|---|---|---|---|
| `Lab1_SpatialTransformations_solution.ipynb` | `SpatialTransformationsTemplate.ipynb`, tasks 1–33 | laptop | fully executed |
| `Lab2_ForwardKinematics_solution.ipynb` | `ForwardKinematicsTemplate.ipynb`, tasks 1–29 | laptop (+ ROS from task 18) | tasks 1–17 executed; ROS cells not executed |
| `Lab3_InverseKinematics_solution.ipynb` | `InverseKinematicsTemplate.ipynb`, tasks 1–18 | laptop | executed; task 18 (robot) not executed |
| `Lab4_DifferentialKinematics_solution.ipynb` | `DifferentialKinematicsTemplate.ipynb`, tasks 1–20 | laptop | executed; tasks 19–20 (robot) not executed |
| `Lab5_TCPCalibration_solution.ipynb` | `TCPCalibrationTemplate.ipynb`, tasks 1–18 | laptop | fully executed |
| `Lab6_TrajectoryPlanning_solution.ipynb` | `TrajectoryPlanningTemplate.ipynb`, tasks 1–19 | laptop | executed; task 19 (robot) not executed |
| `Lab7_SerialCommunication_solution.ipynb` | `SerialCommunicationRobotControlTemplate.ipynb`, tasks 1–29 | Pi | part 1 executed against a **simulated robot**; part 2 (ROS) not executed |
| `Lab8_PickAndPlace_solution.ipynb` | `PickAndPlaceTemplate.ipynb`, tasks 1–28 | Pi | executed against a **simulated** `MyCobot` and GPIO |
| `Lab9_PickAndPlace_MoveIt_solution.ipynb` | `pdfs/Pick_And_Place-2.pdf` (no template) | laptop | algorithms executed on **synthetic** images and data |

Helper files in this folder:
- `labpaths.py`: puts the repo root on `sys.path` (so `helperFunctions` and `serial_iface` import as in the templates) and finds the URDF.
- `hsv_calibrator.py`: the Lab 9 interactive HSV calibrator (`python hsv_calibrator.py image.png`). Its window code was not run here (needs a display); the functions in it are tested in the Lab 9 notebook.

## Safety: nothing here moves the robot by itself
- Cells that talk to the real robot default to **off** (`send_motion`, `publish_traj`, `send_velocity`, `send_ros_motion`, `send_ik`, `enable_motion`, `ALLOW_MOTION`, ...). A person sets them to `True`
  after reading the printed targets, with the workspace clear and the stop within reach.
- Labs 7 and 8 use a **simulated robot** by default (`USE_REAL_ROBOT = False`, `USE_REAL_HARDWARE = False`). On the Pi you switch that on deliberately.
- Targets are relative to the **measured** pose and small; big moves are refused by `check_target` / `check_joint_target_rad` (limits from `gameplan.md` §7). Never send all-zero angles.
- The Lab 7 template's example target `[90, 0, 0, 90, 0, 0]` at speed 100 is a move of up to ~170° per joint at full speed. The solution uses joint 1 + 10° at speed 20 instead.

## The URDF
The labs load `mycobot_280_gazebo.urdf` from the repo root; it is not in the repo yet (Moodle / TAs). Until then `labpaths.urdf_path()` falls back to
`ros2_ws/src/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf`, and prints a note. With that fallback the Lab 5 calibration reproduces the tool offset and base correction
stored in the controller's launch file **to six digits**, so it is very likely the same kinematic chain. When the course file arrives, put it in the repo root and re-run: numbers should not change.

## Where the solutions deliberately differ from the templates
| Lab | Template says / does | Solution does, and why |
|---|---|---|
| 1 | animation `frames=60` with `frame / 60`; task 26 cells in order ψ, ϑ | full angle on the last frame (`frames=61`, `frame / 60`); run ϑ before ψ |
| 1 | `np.arange(0, 1.05, 0.05)` for the SLERP times | `np.linspace(0, 1, 21)`: `arange` with float steps can end above 1.0 and `Slerp` rejects that |
| 2 | random joint vector / all-zero start for the ROS tasks | start from the **measured** pose; check limits and step size before publishing |
| 3 | `least_squares` result used directly | wrap with `transform_to_pipi`: the raw answer can contain 59 rad and violates the joint limits |
| 3 | task 18 publishes the toolbox IK solution | the solution can be 168° away from the current pose; it is refused unless the move is small |
| 4 | task 12/14 sweep joint 2 with all other joints 0 | that pose is already singular (q3 = 0): the curve is flat at 0. Extra sweeps from a healthy pose show where the singularities are (q3 ≈ 0, q5 ≈ ±90°) |
| 4 | resolved-rate control with the plain inverse | the path runs into the elbow singularity (joint 3 jumps 57° in one step); damped inverse and feedback shown |
| 6 | `np.arange(0, tf + dt, dt)` samples | the last sample can be after `tf`, where the deceleration formula turns the velocity negative: the sampler holds the goal |
| 6 | task 19 publishes a trajectory that starts at `q_start` | plans from the measured pose, at 20 Hz, on schedule |
| 7 | target `[90, 0, 0, 90, 0, 0]`, speed 100 | joint 1 + 10° from the measured pose, speed 20, validated |
| 8 | `execute_pick_and_place` without stop checks; `KeyError` for an unknown colour in the middle of the sequence | stop check before every move (as the node does); unknown colour is refused before anything moves |

## Regenerating / editing
The notebooks are ordinary `.ipynb` files: edit them in Jupyter. Cells that need the robot or ROS have no saved output; everything else has.
