import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'mecanum'
    pkg_path = get_package_share_directory(package_name)
    urdf_path = os.path.join(pkg_path, 'urdf', 'mecanum.urdf')
    
    dashboard_path = os.path.realpath(os.path.join(pkg_path, '..', '..', 'lib', package_name, 'mecanum_dashboard.py'))

    world_path = os.path.join(pkg_path, 'worlds', 'hospital.world')

    # GAZEBO_MODEL_PATH để Gazebo tìm thấy các model
    set_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=f"{os.path.join(pkg_path, 'models')}:{os.environ.get('GAZEBO_MODEL_PATH', '')}"
    )

    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()
    robot_desc = robot_desc.replace('$(find mecanum)', pkg_path)

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={'world': world_path}.items()
    )

    
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'mecanum_arm_bot',
            '-x', '2.0',
            '-y', '0.0',
            '-z', '0.03',   
        ],
        output='screen'
    )

    dashboard = ExecuteProcess(
        cmd=['python3', dashboard_path],
        output='screen',
        additional_env={'DISPLAY': os.environ.get('DISPLAY', ':0')}
    )

    load_joint_state_broadcaster = Node(
        package="controller_manager", executable="spawner",
        arguments=["joint_state_broadcaster"]
    )
    load_mecanum_controller = Node(
        package="controller_manager", executable="spawner",
        arguments=["mecanum_controller"]
    )
    load_arm_controller = Node(
        package="controller_manager", executable="spawner",
        arguments=["arm_controller"]
    )
    load_prismatic_controller = Node(
        package="controller_manager", executable="spawner",
        arguments=["prismatic_controller"]
    )

    return LaunchDescription([
        set_model_path,
        rsp,
        gazebo,
        spawn_entity,
        TimerAction(period=3.0, actions=[dashboard]),
        TimerAction(period=5.0, actions=[
            load_joint_state_broadcaster,
            load_mecanum_controller,
            load_arm_controller,
            load_prismatic_controller
        ])
    ])
