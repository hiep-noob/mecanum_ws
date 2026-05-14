from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    

    return LaunchDescription([
        
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[{
                'frame_id': 'base_footprint',      
                'odom_frame_id': 'odom',      
                'subscribe_depth': True,
                'subscribe_scan_cloud': True,
                'subscribe_odom': True,
                'approx_sync': True,
                'use_sim_time': True,
                'queue_size': 100,                 
                'approx_sync_max_interval': 0.1,    
                'wait_for_transform': 0.2,          
                'map_always_update': True,          
            }],
            remappings=[
                ('rgb/image',        '/camera/image_raw'),
                ('depth/image',      '/camera/depth/image_raw'),
                ('rgb/camera_info',  '/camera/camera_info'),
                ('scan_cloud',       '/points_raw'),        
                ('imu',              '/imu'),               
                ('odom',             '/mecanum_controller/odometry'), 
            ],
            arguments=['--delete_db_on_start']        
        ),

        
        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            name='rtabmap_viz',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'frame_id': 'base_footprint',
                'odom_frame_id': 'odom',   
                'subscribe_depth': True,             
                'subscribe_scan_cloud': True,
                'approx_sync': True,
            }],
            remappings=[
                ('rgb/image',        '/camera/image_raw'),
                ('depth/image',      '/camera/depth/image_raw'),
                ('rgb/camera_info',  '/camera/camera_info'),
                ('scan_cloud',       '/points_raw'),
                ('odom',             '/mecanum_controller/odometry'),
            ]
        ),
    ])
