import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Khai báo tham số sử dụng thời gian mô phỏng
    use_sim_time = LaunchConfiguration('use_sim_time')
    
    # 2. Trỏ đúng đến file mecanum.urdf của Hiệp
    pkg_path = get_package_share_directory('mecanum')
    urdf_file = os.path.join(pkg_path, 'urdf', 'mecanum.urdf')

    # Đọc nội dung file URDF
    with open(urdf_file, 'r') as infp:
        robot_description_content = infp.read()
    
    # 3. Cấu hình Node Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': use_sim_time
        }]
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        node_robot_state_publisher
    ])
