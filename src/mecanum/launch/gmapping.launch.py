import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='slam_gmapping',
            executable='slam_gmapping',
            name='slam_gmapping',
            output='screen',
            parameters=[{
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_footprint',
                'use_sim_time': True,
                'maxUrange': 30.0,
                'maxRange': 30.0,
                'minimumScore': 50.0,
                'linearUpdate': 0.1,
                'angularUpdate': 0.1,
                'temporalUpdate': -1.0,
                'particles': 30,
                'delta': 0.05
            }]
        )
    ])
