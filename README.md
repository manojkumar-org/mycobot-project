# mycobot-project

Group repo for the **CoRobot Lab** at TU Dortmund: 9 labs on the myCobot 280 Pi.
Laptop: Ubuntu 24.04 + ROS 2 Jazzy. Robot: its own Raspberry Pi, reached over SSH.

**Project map, robot interface, Lab 7 runbook and game plan: [CLAUDE.md](CLAUDE.md).**

## Layout
```
.
├── CLAUDE.md              project map + game plan (also read automatically by Claude Code)
├── *Template.ipynb        lab notebooks (Labs 1–8): work here
├── helperFunctions.py     used by the IK / Diff / TCP notebooks
├── serial_iface.py        used by Lab 7
├── ros2_ws/src/           Labs 2–7 ROS 2 packages (mycobot_control, mycobot_description)
├── pp_moveit_ws/src/      Lab 9 ROS 2 packages    (brain, vision, controller, interfaces, MoveIt 2 config, mycobot_description)
└── pp_yolo_ws/src/        Lab 8 ROS 2 packages    (vision, mycobot_msgs, mycobot_motion_v1)
```
Three workspaces because `mycobot_description` exists in two course zips and duplicate package names break
`colcon build`. Its two copies are identical (277 MB on disk each, stored once by git), so the first clone takes a while.

**Not in this repo** (get from Moodle): `best.pt` YOLO weights (40 MB, `Lab 09 PP.zip`) → `pp_yolo_ws/weights/`;
`mycobot_280_gazebo.urdf` (Moodle/TAs, in no zip) → repo root, next to the notebooks.

---

## Where to run what
| Labs | Where | How |
|---|---|---|
| 1–6 (maths, RViz2) | laptop | Jupyter on the laptop (§ Laptop) |
| 7–9 (real robot) | robot Pi | Jupyter on the Pi, opened in the laptop browser (§ Robot Pi) |

---

## Robot Pi: bring-up (every session)
The robot is wired to the Pi's serial port `/dev/serial0`. Pi: `cobot-pi1`, 1.8 GB RAM, no swap.

| # | Where | Command |
|---|---|---|
| 1 | laptop | `ssh cobot@129.217.130.85` |
| 2 | Pi | `tmux new -s jup` (or `tmux attach -t jup` if it's still running) |
| 3 | Pi | `source ~/venvs/mycobot/bin/activate && cd ~/mycobot-project && git pull` |
| 4 | Pi | `jupyter lab --no-browser --ip=127.0.0.1 --port 8888`, then detach: **Ctrl+B, D** |
| 5 | laptop, **new** terminal | `ssh -N -L 8888:localhost:8888 cobot@129.217.130.85` (looks frozen = tunnel is up; keep it open) |
| 6 | laptop browser | the `http://127.0.0.1:8888/lab?token=…` link from step 4 (lost it? `jupyter server list` on the Pi) |
| 7 | JupyterLab | open the notebook, kernel *Python 3*, run the check cell |

Check cell:
```python
import sys, os, serial, ipympl
print(sys.executable)                   # /home/cobot/venvs/mycobot/bin/python
print(os.path.exists('/dev/serial0'))   # True
```

**Shut down:** in the notebook `ser.close()`; Pi `tmux attach -t jup` → Ctrl+C twice; laptop Ctrl+C in the tunnel
terminal; commit + `git push` on the Pi; `git credential-cache exit`.

**Rules:** the serial notebook and `mycobot_control` can't hold the port at the same time. Robot-safety rules and
the Lab 7 steps: [CLAUDE.md](CLAUDE.md) §7, §9.

### Robot Pi: one-time setup
1. **Check the Pi:** `ls -l /dev/serial0; groups; free -h`. No `dialout` group? `sudo usermod -aG dialout cobot`,
   then log out and back in.
2. **Clone** as in [Git](#git) below (fine-grained token), then `git checkout myCobot-lab`.
3. **Python environment for Jupyter** (a venv is just a folder, no extra RAM; Ubuntu 24.04 refuses `pip install`
   outside one):
   ```bash
   python3 -m venv --system-site-packages ~/venvs/mycobot && source ~/venvs/mycobot/bin/activate
   python -m pip install jupyterlab ipympl pyserial matplotlib "numpy<2"
   ```
   `--system-site-packages` lets the kernel import ROS's `rclpy` later (Lab 7 Part 2).
4. **Optional Jupyter password** (no new token each start): on the login page paste the token under *Token*, choose a
   *New Password*, click *Log in and set new password*. Don't reuse a personal password (shared Pi).
5. **Laptop SSH key** (no password prompts; also lets Claude Code on the laptop run `ssh` commands, see
   [CLAUDE.md](CLAUDE.md) §6c): `ssh-keygen -t ed25519 && ssh-copy-id cobot@129.217.130.85`
6. **VS Code Remote-SSH** is fine, but **never click "Install in SSH"** for extensions: Pylance, Copilot and Claude
   Code on the Pi filled its RAM and hung it. The "SSH: … Installed" list in the Extensions panel stays empty.
   In that window, *Ports* panel → *Forward a Port* → `8888` replaces bring-up step 5.
7. **Later, Lab 7 Part 2 (ROS):** build the controller once, not while Jupyter runs:
   ```bash
   source /opt/ros/$(ls /opt/ros | head -1)/setup.bash
   cd ~/mycobot-project/ros2_ws
   colcon build --symlink-install --parallel-workers 1 --packages-select mycobot_description mycobot_control
   ```
   From then on, run `source ~/mycobot-project/ros2_ws/install/setup.bash` before starting Jupyter (bring-up step 3).

### Robot Pi: troubleshooting
| Symptom | Fix |
|---|---|
| Jupyter link doesn't open | `127.0.0.1` means the Pi; the laptop needs the tunnel (bring-up step 5) |
| Login page rejects the token | Jupyter was restarted → new token: `jupyter server list` on the Pi |
| Tunnel: `Address already in use` | laptop port 8888 busy → `ssh -N -L 8899:localhost:8888 …`, use `8899` in the link |
| SSH/VS Code: `timed out during banner exchange` | Pi out of memory: `free -h`, `pkill -f vscode-server`, `~/.vscode-server/extensions` must be empty |
| `could not open port /dev/serial0` | no `dialout`, or port busy: `fuser -v /dev/serial0`, close `ser` / stop `mycobot_control` |
| Motors stiff, arm not at home | normal: powered servos hold position. Don't send all-zeros; move from the measured pose ([CLAUDE.md](CLAUDE.md) §7) |

---

## Laptop setup (Labs 1–6)
ROS 2 Jazzy per the [official install guide](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
(details and pitfalls: [CLAUDE.md](CLAUDE.md) §6a). Then:
```bash
python3 -m venv --system-site-packages ~/venvs/mycobot && source ~/venvs/mycobot/bin/activate
python -m pip install jupyterlab ipykernel ipympl roboticstoolbox-python spatialmath-python sympy pyserial pymycobot colcon-common-extensions "numpy<2"
cd ~/mycobot-project/ros2_ws && rosdep install --from-paths src --ignore-src -r -y && colcon build --symlink-install
```
Every session:
```bash
source ~/venvs/mycobot/bin/activate && source ~/mycobot-project/ros2_ws/install/setup.bash
cd ~/mycobot-project && jupyter lab
```
`ipympl` is required: every notebook starts with `%matplotlib widget`. `build/`, `install/`, `log/` are ignored by git.

---

## Git
**Sign in** (per machine). With `gh`: `gh auth login` (GitHub.com → HTTPS → Yes → browser), then `gh auth setup-git`.
Without `gh` or sudo: a fine-grained token (GitHub → Settings → Developer settings → Fine-grained tokens; owner
`manojkumar-org`, only `mycobot-project`, *Contents: Read and write*), kept in memory only:
`git config --global credential.helper 'cache --timeout=36000'`. Username = your GitHub username, password = the token.
**Never save the token in a file inside the repo.**

**Clone and set your identity** (this repo only, never `--global` on a shared machine):
```bash
git clone https://github.com/manojkumar-org/mycobot-project.git && cd mycobot-project
git config user.name  "Your Name"
git config user.email "ID+USERNAME@users.noreply.github.com"    # GitHub → Settings → Emails
printf '\n# personal, this machine only\n.claude/\n.vscode/\npdfs/\n*token*\n.~lock.*#\n' >> .git/info/exclude
git push --dry-run    # "Everything up-to-date" = push access works
```

**Every session:** `git pull --rebase` first; commit; `git push` before you leave.
**Leaving a shared machine:** `gh auth logout` or `git credential-cache exit`; on a shared account also delete the clone.
