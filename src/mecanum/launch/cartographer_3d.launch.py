import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    pkg_share = get_package_share_directory('mecanum')
    
    return LaunchDescription([
        
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '-configuration_directory', os.path.join(pkg_share, 'config'),
                '-configuration_basename', 'cartographer_3d.lua'
            ],
            remappings=[
                ('/points2', '/points_raw'),
                ('/imu', '/imu')            
            ]
        ),
        
       
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            parameters=[{'use_sim_time': True}],
            arguments=['-resolution', '0.05'] 
        ),
    ])
