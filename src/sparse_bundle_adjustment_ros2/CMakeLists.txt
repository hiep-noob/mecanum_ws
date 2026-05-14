cmake_minimum_required(VERSION 3.5)
project(sparse_bundle_adjustment)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(Eigen3 REQUIRED)

include_directories(include ${EIGEN3_INCLUDE_DIRS})
add_definitions(${EIGEN3_DEFINITIONS})
add_definitions(-DSBA_CHOLMOD)

# SBA library
add_library(sba SHARED 
    src/sba.cpp 
    src/spa.cpp 
    src/spa2d.cpp 
    src/csparse.cpp 
    src/proj.cpp 
    src/node.cpp 
    src/sba_file_io.cpp)
target_link_libraries(sba blas lapack cholmod cxsparse)

# standard way for sharing libraries in ament env (ref: ament_index pkg)
ament_export_include_directories(include)
ament_export_interfaces(export_sba)
ament_export_libraries(sba)

ament_package()

install(DIRECTORY include/
        DESTINATION include)

install(TARGETS sba
        EXPORT export_sba
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
