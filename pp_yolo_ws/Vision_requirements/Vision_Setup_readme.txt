1) Create Virtual Environment outside the workspace : python3 venv -m yoloenv
2) Source it :  source path/to/.../yolovenv/bin/activate
3) Install requirements.txt :  python -m pip install --no-cache-dir -r path/to/../requirements.txt
4) Go to your vision workspace : cd path/to/../workspace
5) Source ROS : source /opt/ros/jazzy/setup.bash
6) Inside the venv build your workspace:  colcon build
7) Source your workspace : source install/setup.bash
8) Run your vision node: ros2 run vision vision_node

