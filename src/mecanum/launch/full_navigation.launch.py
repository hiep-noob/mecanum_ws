import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    mecanum_share = get_package_share_directory('mecanum')

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch', 'bringup_launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'map': os.path.join(mecanum_share, 'maps', 'hospital_map_cartographer.yaml'),
            'params_file': os.path.join(mecanum_share, 'config', 'nav2_params.yaml'),
        }.items()
    )

   
    cmd_vel_relay = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        output='screen',
        arguments=['/cmd_vel', '/mecanum_controller/reference_unstamped']
    )

    return LaunchDescription([
        nav2,
        cmd_vel_relay, 
    ])
