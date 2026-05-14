import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    hector_node = Node(
        package='hector_mapping',
        executable='hector_mapping_node',
        name='hector_mapping',
        output='screen',
        parameters=[{
            'use_sim_time': True,           
            'pub_map_odom_transform': True, 
            'map_frame': 'map',
            'base_frame': 'base_link',      
            'odom_frame': 'base_link',      
            'scan_topic': 'scan',
            'map_resolution': 0.05,
            'map_size': 2048,
            'map_start_x': 0.5,
            'map_start_y': 0.5,
            'map_multi_res_levels': 2,
            
            # Cấu hình cập nhật bản đồ
            'update_factor_free': 0.4,
            'update_factor_occupied': 0.9,    
            'map_update_distance_thresh': 0.4,
            'map_update_angle_thresh': 0.06,
            
            # Cấu hình Lidar
            'laser_z_min_value': -1.0,
            'laser_z_max_value': 1.0,
            'laser_min_dist': 0.25,        
            'laser_max_dist': 12.0
        }]
    )

    return LaunchDescription([hector_node])
