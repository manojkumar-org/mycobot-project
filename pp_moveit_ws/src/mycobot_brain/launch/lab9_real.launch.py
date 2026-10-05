"""Lab 9 on the real robot, Lab PC side: MoveIt, camera and vision_lab9, each in its own gnome-terminal tab.

The controller runs on the Pi (started by hand). brain_lab9 is NOT started here: start it last, after the checks
in solutions/lab9_real_hardware/README.md, because it moves the arm home as soon as it starts.
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess


def tab(title, cmd):
    return ExecuteProcess(cmd=["gnome-terminal", "--tab", f"--title={title}", "--"] + cmd, output="screen")


def generate_launch_description():
    return LaunchDescription([
        tab("MoveIt", ["ros2", "launch", "mycobot_280_moveit2", "move_group.launch.py"]),
        tab("Camera", ["ros2", "run", "mycobot_280pi", "opencv_camera"]),
        tab("Vision", ["ros2", "run", "mycobot_vision", "vision_lab9"]),
    ])
