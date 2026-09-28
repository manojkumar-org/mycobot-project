# mycobot-project

Group repo for the **CoRobot Lab** at TU Dortmund (myCobot 280 Pi, ROS 2 Jazzy on Ubuntu 24.04).
Setup: ROS 2 Jazzy per the [official install guide](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
and the course PDF `SystemSetup_Ubuntu_ROS2.pdf` (Moodle).

**Project map, robot interface and game plan: see [CLAUDE.md](CLAUDE.md).**

## Layout
```
.
├── CLAUDE.md              project map + game plan (also read automatically by Claude Code)
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
the files only once (about 37 MB compressed). The first clone takes a while.

## Not in this repo: get them from Moodle
| What | Size | Where it goes | From |
|---|---|---|---|
| `best.pt` (YOLO weights) | 40 MB | `pp_yolo_ws/weights/` | `Lab 09 PP.zip` |
| `mycobot_280_gazebo.urdf` | — | repo root (next to the notebooks) | Moodle / TAs (not in any zip) |

## Set up on a new machine (lab PC, own laptop)
**1. Sign in to GitHub.** With `gh` (or sudo to `sudo apt install gh`):
```bash
gh auth login        # GitHub.com → HTTPS → Yes (authenticate Git) → Login with a web browser
gh auth setup-git
```
Without `gh` or sudo: create a fine-grained token on GitHub (Settings → Developer settings → Fine-grained tokens,
only `mycobot-project`, *Contents: Read and write*, expires at course end). Then keep it in memory only:
`git config --global credential.helper 'cache --timeout=36000'`. When git asks, the username is your GitHub
username and the password is the token.

**2. Clone and set your identity** (for this repo only, never `--global` on a shared PC):
```bash
git clone https://github.com/manojkumar-org/mycobot-project.git && cd mycobot-project
git config user.name  "Your Name"
git config user.email "ID+USERNAME@users.noreply.github.com"    # GitHub → Settings → Emails
printf '\n# personal, this PC only\n.claude/\n.vscode/\npdfs/\n.~lock.*#\n' >> .git/info/exclude
git push --dry-run   # "Everything up-to-date" = push access works
```

**3. Python environment** (the notebooks and `colcon` run from it):
```bash
python3 -m venv --system-site-packages ~/venvs/mycobot && source ~/venvs/mycobot/bin/activate
python -m pip install jupyterlab ipykernel ipympl roboticstoolbox-python spatialmath-python sympy pyserial pymycobot colcon-common-extensions "numpy<2"
```
`ipympl` is required: every notebook starts with `%matplotlib widget`.

## Build (after ROS 2 Jazzy is installed)
```bash
source ~/venvs/mycobot/bin/activate
cd ros2_ws && rosdep install --from-paths src --ignore-src -r -y && colcon build --symlink-install
```
`build/`, `install/` and `log/` are ignored by git.

## Every session
```bash
git pull --rebase    # first: get what others (or you, from another machine) pushed
# … work, commit …
git push             # before you leave
```
**Leaving a shared PC:** run `gh auth logout` or `git credential-cache exit`. On a shared account, also delete the clone.

## Work on the robot Pi (Labs 7–9, over SSH)
The robot is wired to the Pi's serial port `/dev/serial0`, so Labs 7–9 (serial notebook, `mycobot_control`,
pick & place) run **on the Pi**. The laptop is only the screen.
```bash
ssh cobot@129.217.130.85
```

**1. Check the Pi** (once):
```bash
lsb_release -ds; uname -m; ls /opt/ros; python3 --version; free -h
ls -l /dev/serial0; groups          # 'dialout' needed for the serial port
ping -c1 -W2 github.com >/dev/null && echo "internet ok" || echo "NO internet"
```

**2. Clone** with steps 1–2 above (fine-grained token + `credential.helper cache`), then `git checkout myCobot-lab`.

**3. Connect VS Code** (on the laptop): install the **Remote - SSH** extension → Ctrl+Shift+P →
*Remote-SSH: Connect to Host…* → `cobot@129.217.130.85` → *File → Open Folder* → `~/mycobot-project`.
The status bar shows `SSH: 129.217.130.85`; every terminal in this window now runs on the Pi.
Password on every connect? Once on the laptop: `ssh-keygen -t ed25519 && ssh-copy-id cobot@129.217.130.85`.

**4. Python environment on the Pi** (in a VS Code terminal):
```bash
python3 -m venv --system-site-packages ~/venvs/mycobot && source ~/venvs/mycobot/bin/activate
python -m pip install jupyterlab ipykernel ipympl pyserial pymycobot "numpy<2"
python -m ipykernel install --user --name mycobot --display-name "Python (mycobot)"
```

**5. Make ROS visible to the notebook kernel.** A kernel started by VS Code doesn't run your `source` commands,
so put them in `~/.bashrc` on the Pi (replace `<distro>` with what `ls /opt/ros` printed):
```bash
cat >> ~/.bashrc <<'EOF'
source /opt/ros/<distro>/setup.bash
[ -f ~/mycobot-project/ros2_ws/install/setup.bash ] && source ~/mycobot-project/ros2_ws/install/setup.bash
EOF
source ~/.bashrc
cd ~/mycobot-project/ros2_ws && colcon build --symlink-install --packages-select mycobot_description mycobot_control
```
Then Ctrl+Shift+P → *Remote-SSH: Kill VS Code Server on Host…*, and reconnect, so VS Code picks up the new environment.

**6a. Jupyter inside VS Code** (recommended): in the SSH window install the **Python** and **Jupyter** extensions
(button *Install in SSH: …*). Open a notebook → *Select Kernel* → *Jupyter Kernel…* → **Python (mycobot)**.

**6b. Or JupyterLab in the laptop browser:**
```bash
# laptop: forward the port
ssh -L 8888:localhost:8888 cobot@129.217.130.85
# Pi (inside that ssh, ideally in tmux so it survives disconnects)
source ~/venvs/mycobot/bin/activate && cd ~/mycobot-project && jupyter lab --no-browser --port 8888
```
Open the `http://localhost:8888/?token=…` link it prints, on the laptop.

**7. Check** in a notebook cell:
```python
import sys, os, serial, ipympl
print(sys.executable)                   # ~/venvs/mycobot/bin/python
print(os.path.exists('/dev/serial0'))   # True
import rclpy; print("ROS ok")           # fails → step 5 not picked up (reconnect VS Code)
```

**Rules on the Pi:** the serial notebook and `mycobot_control` can't hold the port at the same time
(`fuser -v /dev/serial0`); run the controller in `tmux`. Robot-safety rules and the Lab 7 runbook: [CLAUDE.md](CLAUDE.md) §7, §9.
**Leaving:** push your work, then `git credential-cache exit` (and `/logout` if you used Claude Code on the Pi).
