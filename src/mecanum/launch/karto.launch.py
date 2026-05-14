import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='slam_karto',
            executable='slam_karto',
            name='slam_karto',
            output='screen',
            parameters=[{
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_footprint',
                'use_sim_time': True,
                'resolution': 0.05,
                'do_loop_closing': True
            }]
        )
    ])
