cmake_minimum_required(VERSION 3.8)
project(mecanum)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


find_package(ament_cmake REQUIRED)
find_package(robot_state_publisher REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(gazebo_ros2_control REQUIRED)
find_package(ros2_control REQUIRED)
find_package(ros2_controllers REQUIRED)


install(DIRECTORY launch urdf meshes rviz config worlds models maps
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/teleop_node.py            
  src/arm_teleop.py
  src/mecanum_control.py
  src/mecanum_drive_controller.py
  mecanum_dashboard.py     
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()
ament_export_dependencies(robot_state_publisher gazebo_ros gazebo_ros2_control ros2_control ros2_controllers)
ament_export_include_directories(include)
ament_package()

