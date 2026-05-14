from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mecanum',
            executable='teleop_node',   # tên entry point trong setup.py, không có .py
            name='keyboard_teleop',
            output='screen',
            prefix='xterm -e',
            parameters=[{'use_sim_time': True}],
        ),
    ])
