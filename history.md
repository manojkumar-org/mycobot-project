# History

Compact log of what changed, newest first. Details and current state: [gameplan.md](gameplan.md), setup: [README.md](README.md).

## 2026-10-04 (home laptop, uncommitted)

- Labs 3–7 solutions rewritten from the original templates: code cells = template cells with the blanks filled (Lab 3:
  +24/−8 changed lines of 346, Lab 7: +43/−25 of 220); per task **Concept**, **How it works** (syntax), **Example** blocks.
  **Real robot by default** in the robot tasks (Lab 3 task 18, Lab 4 tasks 19–20, Lab 6 task 19, Lab 7 Parts 1–2), each
  with a short guard; optional 🧪 simulation blocks after the real solution.
- New `solutions/sim_robot.py`: simulated arm behind a virtual serial port, so the real `serial_iface.py` and the real
  `mycobot_control` run unchanged (isolated with `ROS_DOMAIN_ID=99`, localhost only). All robot cells of Labs 3, 4, 6, 7
  were run end to end against it.
- Found in that test (code reading + simulation, not yet on the robot): `/mycobot/joint_states` is an estimate that lags
  one position command; after a velocity stop the controller has sent STOP and ignores-until-resume applies to later
  position commands; the parked pose (joint 5 ≈ 90°) is wrist-singular. The notebooks explain and work around all three.
- `solutions/labpaths.py`: registers `ros2_ws/src` so the course URDF's `package://mycobot_description` meshes resolve
  without a sourced workspace (the solutions failed at the URDF cell before). `solutions/README.md` updated.

## 2026-10-02 afternoon (Lab PC, Lab 9 on real hardware)

- New `solutions/lab9_simple/` (camera + YOLO on the Lab PC → `/simple_pp/target` → Lab 8 pick-and-place on the Pi; no
  MoveIt). Committed as `9013a6c`; lab edits after it uncommitted. Status, incidents and the next fix:
  [solutions/lab9_simple/STATUS.md](solutions/lab9_simple/STATUS.md).
- Works: ultralytics in `~/venvs/mycobot`, markers + YOLO on the live camera, ROS link to the Pi, Pi ran the pick sequence.
- `best.pt` (`Lab 09 PP.zip`) → `pp_yolo_ws/weights/` (gitignored); `mycobot_280_gazebo.urdf` (`Common.zip`) → repo root.
  Other zip contents identical to the repo.
- Wrong: the camera → robot mapping (hand-measured marker values, camera or plate moved between runs). `--jog` collided
  the arm with itself → not to be used. Lab cubes are 35 mm, not 40.
- Next: robot-taught calibration (STATUS §6), then the bins.

## 2026-10-02 (home laptop, all uncommitted)

### Docs
- tmux replaced by plain terminals in `README.md`, `gameplan.md`, the run guide ("Terminals without tmux", end of §4):
  one terminal per process; `nohup … &` + `kill` only for Jupyter, never for the controller. `nohup` lines untested on the Pi.
- `lab9_runbook.md` merged into `solutions/Lab8_Lab9_run_guide.md` (lab values kept as written: IPs, domain 47, UFW,
  camera `/dev/video0` C930e, A1–A6 done, A7 TODO) and deleted. Status values copied from the lab notes, not re-verified.
- Two editing sessions worked in the same working tree in the morning; the second one was closed. All edits are in the tree.

### Lab 9 approach for the real system
- Decision: no simulated or synthetic test bench for the final lab. Two approaches, **A + B** or **B + C**, both implemented
  in `solutions/lab9_real_hardware/`: `GUIDE.md` (Part 0, Tasks A, B, C step by step, code explained) + `record_frames.py`,
  `camera_intrinsics.py`, `markers.yaml` (placeholders), `aruco_extrinsics.py`, `position_errors.py`, `evaluate_detection.py`,
  `hsv_calibrate.py`, `evaluate_thresholds.py`, reference `vision_AB.py` / `vision_B.py`. Results go to `lab9/`.
- Tested on the laptop with generated images only: camera pose from 2 markers within 2.3 mm / 0.3°, cube positions within
  0.4 mm, yaw within 0.6°, checkerboard K within 0.3 %, B evaluation and stale test, C hue split at 0/179.
  Not tested: `record_frames.py`, the service call of `position_errors.py`, the click windows; nothing tested in the lab yet.
- Old Lab 9 notebook and its helpers (`lab9_synthetic.py`, `publish_test_image.py`, `hsv_calibrator.py`) moved unchanged to
  `solutions/lab9_old_synthetic/`. Pointers updated in `solutions/README.md`, the run guide and gameplan §7b.
- Code findings (for the Part 0 report): `cv2.contourArea` counts holes (solidity check added in Task B); sort-mode
  rejoice (`brain.py:526`) is never reached because the menus call themselves (check in the lab; the run guide says
  rejoice after every run); stacking with red missing keeps green on the pump; `opencv_camera.py` reopens the camera for
  every frame (check the real rate); `mycobot_vision/setup.py` lists a `vision2` entry point without a file.

### Open, in priority order
1. Lab session 1: A7 network test → Part 0 (GUIDE §4, incl. `position_errors.py baseline`) → record frames (GUIDE §5);
   measure marker poses and camera height; checkerboard available?
2. Send the test-setup details (ArUco dictionary, ids, size, poses) → fill `markers.yaml`, adapt the marker step if needed.
3. Choose the approach after session 1 (markers + checkerboard → A + B, else B + C).
4. Commit and push today's changes (moves, deletion of `lab9_runbook.md`, edited docs, new folder).
5. Part 0 report; Lab 7/8 PDF short questions.

## 2026-10-01 (written 2026-10-02, from `git log` and `gameplan.md` §12; robot-side facts are as logged in the lab)

### Git
- Merge `92778ab` (15:01) joined the home commit `55eb47c` with `8a93ca3`; no conflicts, `solutions/` untouched by the merge.
- `a6098b7` (15:24) merged `myCobot-personal` into `myCobot-lab`. Lab commits after it: `245fc7c` Lab 7 robot run,
  `fb4d71c` Lab 8 robot run + Lab 8/9 solution notebooks, `79dcab8` README credential cache, `c472ce3` Lab 9 setup + game plan.
- State on 2026-10-02: laptop is on `myCobot-lab` = `origin/myCobot-lab` (`c472ce3`); local `myCobot-personal` (`92778ab`) is
  4 commits behind its origin. **Uncommitted:** `README.md`, `gameplan.md`, `history.md`, `solutions/README.md`,
  `solutions/Lab8_Lab9_run_guide.md`; `lab9_runbook.md` deleted (its content now lives in the run guide).

### Solutions (home work, commit `55eb47c`)
- Labs 1, 2, 8, 9 reworked so the code cells follow the template (blanks filled); the explanations, "How it works" and
  syntax examples were kept.
- Lab 8 ran against a simulated `MyCobot` / GPIO (`sim_hardware.py`); Lab 9 algorithms ran on synthetic data
  (`lab9_synthetic.py`); `publish_test_image.py` feeds a test image to `camera/image`.
- `solutions/Lab8_Lab9_run_guide.md`: machine split, files per machine, SSH steps, start order, values and experiments.

### Lab (robot)
- Lab 7 Part 1 + Part 2 and **Lab 8 done on the robot** (Pi: `python3-rpi-lgpio` for `RPi.GPIO`, `ros-jazzy-control-msgs`).
- Lab 9 setup A1–A6 done on the Lab PC `CoRobot2`; ROS domain 47 on both machines. A7 (network test) not yet run.
- Decision: no simulated or synthetic test bench for the final lab; use the real camera, robot and pump.

### Open, in priority order
1. Lab 9: A7 multicast test → accuracy check with a ruler → first sort run (guide §6).
2. Step-by-step real-hardware approach for the Lab 9 task (new file, the old solution stays as reference).
3. Part 0 report; choose the 2 tasks (gameplan §7b); Lab 7/8 PDF short questions.
4. Test-setup details (ArUco marker layout) still to be added by Mano; then adapt the marker pipeline.

## 2026-09-30 (written 12:30)

### Git
- `myCobot-lab` fast-forwarded to `070cdf2` (= `myCobot-personal` incl. `solutions/`) and pushed. Workflow: edit at home on
  `myCobot-personal` → update `myCobot-lab` when it works → `git pull` on the Pi.
- Pi token cache had expired (10 h); re-entered, Pi pulled to `070cdf2`.
- **Uncommitted:** laptop `README.md`, `gameplan.md`, `SerialCommunicationRobotControlTemplate.ipynb`, `history.md`;
  Pi `SerialCommunicationRobotControlTemplate.ipynb`, `solutions/Lab7_SerialCommunication_solution.ipynb`.

### Laptop ↔ Pi access
- SSH key `~/.ssh/id_ed25519`; `~/.ssh/config` alias `cobot` with connection reuse (1st call 0.96 s, next 0.04 s).
  Backup: `~/.ssh/config.bak-2026-09-30`.
- Workflow decided: VS Code Remote-SSH with **zero extensions on the Pi**; JupyterLab `--no-browser` on the Pi, opened in
  the laptop browser via port forwarding. Jupyter/Python/Pylance had been installed on the Pi again → now removed
  (`~/.vscode-server/extensions` empty).
- Two Jupyter servers were running (8888, 8889); 8888 stopped. 8889 (serves `/home/cobot`) is **not in tmux**.

### Pi facts (checked)
- Raspberry Pi 4B, Ubuntu 24.04.5, ROS 2 Jazzy, 1.8 GB RAM, no swap, internet OK.
- Robot UART = **`/dev/ttyAMA0`** (device-tree alias `serial0`, `dtoverlay=disable-bt`). Ubuntu has no `/dev/serial0` link
  → created `/etc/udev/rules.d/99-serial0.rules` (`serial0 -> ttyAMA0`), verified.
- Per-lab software: Pi has what Lab 7 needs; lacks `roboticstoolbox`/`spatialmath` (Lab 2 notebook), `RPi.GPIO`, `cv2`,
  YOLO/torch (Lab 8), MoveIt (Lab 9). **Camera is on the laptop.** Labs 3–5 won't run on the Pi (decision).

### Lab 7 (Serial Communication)
- Part 1: task 9 had target `[90, 0, 0, 90, 0, 0]` at speed 100 (too large). Robot first ignored commands; after a
  system restart the move executed. Cause of "sent but not moving" **unconfirmed** (likely stop/pause state).
  Arm now at ≈ `[91°, 0.6°, 0.5°, 91°, -0.6°, 0.6°]`.
- Part 2: `mycobot_control` built and launched (`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`); `/mycobot/joint_states`
  verified. Task 19 needed a spin loop (single `spin_once` missed the first message). Tasks 20–27 walked through
  (21: J1 +10° via `/mycobot/joint_command`; 23: 0.1 rad/s × 1.5 s on J1; 24: J1 −10° + recording; 25–27).

### Docs
- README: "How it runs" diagram, `ssh cobot`, `ttyAMA0`, **[Pi]** markers, setup step 2 (udev link), step 6 (SSH config).
- gameplan: Pi facts, per-lab Pi software table, §9 rule 8 ([Pi] steps by a person), §10/§11 (Q6: laptop/Pi split), §12.
- `~/.claude/CLAUDE.md` (working rules) created.

### Open, in priority order
1. Lab 7 tasks 28–29 and the PDF short questions; save the notebook.
2. Run the controller and Jupyter each in its **own SSH terminal, kept open** (no tmux needed). If they must survive a closed
   window: `nohup … > log 2>&1 &` and `kill` by pid.
3. Matplotlib mix in the venv (3.11.2 pip vs system `mpl_toolkits` 3.6.3 → "Unable to import Axes3D"). Proposed fix,
   **not applied:** `~/venvs/mycobot/bin/pip uninstall -y matplotlib types-seaborn`.
4. Commit and push today's changes (see Git).
5. Ask the TAs: laptop/Pi split for Labs 2, 8, 9; `ROS_DOMAIN_ID`; swap and the udev rule on the shared Pi.
