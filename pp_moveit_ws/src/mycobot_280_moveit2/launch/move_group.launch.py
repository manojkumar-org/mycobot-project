from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("firefighter", package_name="mycobot_280_moveit2").to_moveit_configs()
    
    moveit_config.trajectory_execution.update({                         # yannick: added this to fix a planning error
        "trajectory_execution.allowed_start_tolerance": 0.3,            # where two joints deviated
                                                                        # more than 0.01 from start state
        # Lab 9 (10-05): the real controller sends each waypoint over serial and sleeps, so it is always slower than
        # the plan; with the defaults (x1.2 + 0.5 s) every execution ended TIMED_OUT while the arm kept moving
        "trajectory_execution.allowed_execution_duration_scaling": 4.0,
        "trajectory_execution.allowed_goal_duration_margin": 5.0,
    })

    return generate_move_group_launch(moveit_config)
