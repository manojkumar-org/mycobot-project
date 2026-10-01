# History

Compact log of what changed, newest first. Details and current state: [gameplan.md](gameplan.md), setup: [README.md](README.md).

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
2. Run the controller and Jupyter **inside tmux** (`ctl`, `jup`), so a closed terminal doesn't stop them.
3. Matplotlib mix in the venv (3.11.2 pip vs system `mpl_toolkits` 3.6.3 → "Unable to import Axes3D"). Proposed fix,
   **not applied:** `~/venvs/mycobot/bin/pip uninstall -y matplotlib types-seaborn`.
4. Commit and push today's changes (see Git).
5. Ask the TAs: laptop/Pi split for Labs 2, 8, 9; `ROS_DOMAIN_ID`; swap and the udev rule on the shared Pi.
