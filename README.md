# mycobot-project

Group repo for the **CoRobot Lab** at TU Dortmund: 9 labs on the myCobot 280 Pi.
Laptop: Ubuntu 24.04 + ROS 2 Jazzy. The robot has its own Raspberry Pi; you reach it over SSH.

**Robot interface, Lab 7 runbook, rules and game plan: [gameplan.md](gameplan.md).**

## What's in the repo
```
.
├── gameplan.md            project map + game plan
├── *Template.ipynb        lab notebooks (Labs 1–8): work here
├── helperFunctions.py     used by the IK / Diff / TCP notebooks
├── serial_iface.py        used by Lab 7
├── solutions/             worked solutions with explanations (one notebook per lab)
├── ros2_ws/src/           Labs 2–7 (mycobot_control, mycobot_description)
├── pp_moveit_ws/src/      Lab 9    (brain, vision, controller, interfaces, MoveIt 2 config, mycobot_description)
└── pp_yolo_ws/src/        Lab 8    (vision, mycobot_msgs, mycobot_motion_v1)
```
- **Why three workspaces:** `mycobot_description` is in two course zips, and `colcon build` fails on duplicate
  package names. The two copies are identical (277 MB on disk each, stored once by git), so the first clone is slow.
- **Get these from Moodle** (not in the repo):
  - `best.pt` (Lab 8 YOLO weights, 40 MB, in `Lab 09 PP.zip`) → `pp_yolo_ws/weights/`
  - `mycobot_280_gazebo.urdf` (ask the TAs, it's in no zip) → repo root, next to the notebooks

Commands below assume the clone is at `~/mycobot-project`. If yours is somewhere else, use your folder.

| Labs | Run on | Section |
|---|---|---|
| 1–6 (maths, RViz2) | laptop | [Laptop](#laptop-labs-16) |
| 7–9 (real robot) | robot Pi, opened in the laptop browser | [Robot Pi](#robot-pi-labs-79) |

---

## How it runs
```
LAPTOP (CoRobot2)                          SSH                ROBOT PI (cobot-pi1)                     ROBOT
browser ──────── tunnel localhost:8888 ─────────────▶ JupyterLab in tmux "jup" ─ notebook kernel
terminal ─────── ssh cobot ─────────────────────────▶ shell: tmux, ros2, git          │
VS Code ──────── Remote-SSH (no extensions on Pi) ──▶ ~/mycobot-project               ▼
Claude Code ──── ssh cobot '<read-only cmd>' ───────▶ checks, logs, topics       /dev/ttyAMA0 ── UART 1 Mbaud ──▶ myCobot 280
```
- **Everything that touches the robot runs on the Pi.** The laptop only shows it: browser, terminal, VS Code.
- **`ssh cobot`** is an alias in the laptop's `~/.ssh/config` (key `~/.ssh/id_ed25519`, one shared connection
  that stays open 10 min, so repeated calls are fast and light on the Pi). Setup: [One-time setup](#one-time-setup), step 6.
- **Serial port:** the robot is on `/dev/ttyAMA0`. The course code opens `/dev/serial0`, a link that Ubuntu doesn't
  create by itself (setup step 2).
- **Code flow:** edit at home on `myCobot-personal` → push → update `myCobot-lab` once it works → `git pull` on the Pi
  (the Pi tracks `myCobot-lab`).
- **[Pi]** marks commands you type on the Pi yourself (they need sudo, a token or a password). Claude Code on the
  laptop only runs read-only `ssh cobot` checks and never moves the robot.

---

## Robot Pi (Labs 7–9)
Pi `cobot-pi1` (Raspberry Pi 4B, Ubuntu 24.04.5, ROS 2 Jazzy), login `ssh cobot` (= `cobot@129.217.130.85`).
The robot is on the Pi's UART `/dev/ttyAMA0`; `/dev/serial0` is a link to it (setup step 2).
The Pi has only 1.8 GB RAM and no swap, so keep it light.

### Start (every session)
1. **Laptop, terminal 1:** log in to the Pi.
   ```bash
   ssh cobot                # without the alias (setup step 6): ssh cobot@129.217.130.85
   ```
2. **[Pi] Same terminal, now on the Pi:** start Jupyter inside tmux, so it keeps running if SSH drops.
   ```bash
   tmux new -s jup          # "duplicate session"? then: tmux attach -t jup
   source ~/venvs/mycobot/bin/activate && cd ~/mycobot-project && git pull
   jupyter lab --no-browser --ip=127.0.0.1 --port 8888
   ```
   Copy the `http://127.0.0.1:8888/lab?token=…` link it prints. Then detach with **Ctrl+B, then D**.
3. **Laptop, terminal 2 (new):** open the tunnel. It looks frozen when it works; leave it open.
   ```bash
   ssh -N -L 8888:localhost:8888 cobot
   ```
4. **Laptop browser:** open the link. (Lost it? Run `jupyter server list` on the Pi.)
5. **JupyterLab:** open the notebook, choose kernel *Python 3*, and run this check first:
   ```python
   import sys, os, serial, ipympl
   print(sys.executable)                   # /home/cobot/venvs/mycobot/bin/python
   print(os.path.exists('/dev/ttyAMA0'))   # True: the robot's port
   print(os.path.exists('/dev/serial0'))   # True once setup step 2 is done
   ```

### Stop
1. **Notebook:** run `ser.close()`, then save.
2. **[Pi] Terminal 1:** `tmux attach -t jup`, press **Ctrl+C twice** to stop Jupyter.
3. **Same terminal:** commit and `git push`, then `git credential-cache exit` (forgets the token), then `exit`
   twice (closes tmux, then SSH).
4. **Terminal 2 (laptop):** **Ctrl+C** closes the tunnel.

**Rules:** the serial notebook and `mycobot_control` can't use the port at the same time.
Robot-safety rules and the Lab 7 steps: [gameplan.md](gameplan.md) §7, §9.

### One-time setup
Redo these on a new Pi or a fresh SD card. What's already done is tracked in [gameplan.md](gameplan.md) §6b.
1. **[Pi] Serial access:** run `ls -l /dev/ttyAMA0; groups; free -h`. If `groups` doesn't list `dialout`:
   `sudo usermod -aG dialout cobot`, then log out and back in.
2. **[Pi] Create the `/dev/serial0` link.** The robot code for Labs 7–9 (`mycobot_control`, `motion_node.py`,
   `controller.py`) opens `/dev/serial0`. Raspberry Pi OS creates that link; this Ubuntu image doesn't. On this Pi the
   robot UART is `ttyAMA0` (`dtoverlay=disable-bt` in `/boot/firmware/config.txt`), so link it:
   ```bash
   echo 'KERNEL=="ttyAMA0", SYMLINK+="serial0", GROUP="dialout", MODE="0660"' | sudo tee /etc/udev/rules.d/99-serial0.rules
   sudo udevadm control --reload && sudo udevadm trigger
   ls -l /dev/serial0          # expect: /dev/serial0 -> ttyAMA0
   ```
   The rule survives reboots. Undo: `sudo rm /etc/udev/rules.d/99-serial0.rules`, then reboot.
3. **Clone** as in [Git](#git), signing in with a token.
4. **[Pi] Python environment for Jupyter** (Ubuntu 24.04 only allows `pip install` inside a venv; a venv costs no RAM):
   ```bash
   python3 -m venv --system-site-packages ~/venvs/mycobot && source ~/venvs/mycobot/bin/activate
   python -m pip install jupyterlab ipympl pyserial matplotlib "numpy<2"
   ```
   `--system-site-packages` lets the notebook use ROS's `rclpy` later (Lab 7 Part 2).
5. **Jupyter password (optional, so you don't need a new token every start):** on the Jupyter login page, paste
   the token under *Token*, type a *New Password*, click *Log in and set new password*.
   The Pi is shared, so don't reuse a personal password.
6. **Laptop: SSH key and the `cobot` alias.** No password prompts, and Claude Code on the laptop can run `ssh cobot`.
   ```bash
   ssh-keygen -t ed25519 && ssh-copy-id cobot@129.217.130.85
   ```
   Then put this in the laptop's `~/.ssh/config`:
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
   Test: `ssh -o BatchMode=yes cobot hostname` prints `cobot-pi1` without asking for a password.
7. **VS Code Remote-SSH is fine, but never click "Install in SSH" on an extension.** Pylance and Copilot on
   the Pi filled its RAM and hung it. The "SSH: … Installed" list in Extensions must stay empty.
   Tip: in that window, *Ports* panel → *Forward a Port* → `8888` replaces the tunnel (Start, step 3).
8. **[Pi] Lab 7 Part 2 (ROS), once:** build the controller while Jupyter is **stopped**.
   ```bash
   source /opt/ros/jazzy/setup.bash
   cd ~/mycobot-project/ros2_ws
   colcon build --symlink-install --parallel-workers 1 --packages-select mycobot_description mycobot_control
   ```
   From then on, in Start step 2, also run `source ~/mycobot-project/ros2_ws/install/setup.bash`
   before `jupyter lab`.

### Troubleshooting
| Problem | Fix |
|---|---|
| Jupyter link doesn't open | The tunnel isn't running: Start, step 3. (`127.0.0.1` in the link means "this machine".) |
| Login page rejects the token | Jupyter was restarted and has a new token: `jupyter server list` on the Pi |
| Tunnel says `Address already in use` | Laptop port 8888 is busy. Use `ssh -N -L 8899:localhost:8888 …` and `8899` in the link |
| SSH or VS Code: `timed out during banner exchange` | The Pi is out of memory: `free -h`, `pkill -f vscode-server`; `~/.vscode-server/extensions` must be empty |
| `could not open port /dev/serial0` | The link is missing: setup step 2. The notebook can also use `/dev/ttyAMA0` directly |
| `could not open port /dev/ttyAMA0` | No `dialout` group (setup step 1), or something else holds the port: `fuser -v /dev/ttyAMA0`, then `ser.close()` or stop `mycobot_control` |
| `bash: warning: setlocale: LC_ALL: cannot change locale` on every SSH command | Harmless: the laptop sends `LC_ALL=en_US.UTF-8`, which the Pi doesn't have. To silence it: **[Pi]** `sudo locale-gen en_US.UTF-8` |
| Motors stiff, arm not at home | Normal: powered servos hold their position. Never send all-zeros; move from the measured pose ([gameplan.md](gameplan.md) §7) |

---

## Laptop (Labs 1–6)
**Once:** install ROS 2 Jazzy with the [official guide](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
(pitfalls: [gameplan.md](gameplan.md) §6a), then:
```bash
python3 -m venv --system-site-packages ~/venvs/mycobot && source ~/venvs/mycobot/bin/activate
python -m pip install jupyterlab ipykernel ipympl roboticstoolbox-python spatialmath-python sympy pyserial pymycobot colcon-common-extensions "numpy<2"
cd ~/mycobot-project/ros2_ws && rosdep install --from-paths src --ignore-src -r -y && colcon build --symlink-install
```
**Every session:**
```bash
source ~/venvs/mycobot/bin/activate && source ~/mycobot-project/ros2_ws/install/setup.bash
cd ~/mycobot-project && jupyter lab
```
You need `ipympl`: every notebook starts with `%matplotlib widget`. `build/`, `install/`, `log/` are ignored by git.

---

## Git
### Sign in (once per machine)
- **Your own laptop, with `gh`:** `gh auth login` (GitHub.com → HTTPS → Yes → browser), then `gh auth setup-git`.
- **Pi or lab PC, no `gh` or sudo:** create a fine-grained token: GitHub → Settings → Developer settings →
  Fine-grained tokens. Owner `manojkumar-org`, only `mycobot-project`, *Contents: Read and write*.
  Keep it in memory only, for 15 days (15 × 24 × 3600 s):
  ```bash
  git config --global credential.helper 'cache --timeout=1296000'
  ```
  When git asks: username = your GitHub username, password = the token.
  The cache lives in RAM: a **reboot forgets it** and git asks once more. Check it's set: `git config --global credential.helper`.
  **Never save the token in a file inside the repo.**

### Clone and set your name (once per machine)
Set your name for this repo only. Never use `--global` on a shared machine.
```bash
git clone https://github.com/manojkumar-org/mycobot-project.git && cd mycobot-project
git checkout myCobot-lab                                         # the work branch
git config user.name  "Your Name"
git config user.email "ID+USERNAME@users.noreply.github.com"    # GitHub → Settings → Emails
printf '\n# personal, this machine only\n.vscode/\npdfs/\n*token*\n.~lock.*#\n' >> .git/info/exclude
git push --dry-run                                               # "Everything up-to-date" = you can push
```

### Every session
- **Start:** `git pull --rebase`.
- **End:** commit, then `git push` before you leave.
- **Leaving a shared machine:** `gh auth logout` or `git credential-cache exit`. On a shared account, also delete
  the clone.
