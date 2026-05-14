# Sparse Bundle Adjustment Library (ROS 2)  
This is ROS 2 version pkg for Sparse Bundle Adjustment Library (needed for slam_karto_ros2)  
The original repo (ROS 1) was developed at Willow Garage as part of the vslam stack.  
(original repo: https://github.com/ros-perception/sparse_bundle_adjustment)  

## Developer  
* HaoChih, LIN (haochih.lin@adlinktech.com)  

## License  
BSD License (adhere to original ROS 1 sparse_bundle_adjustment pkg)  
  
## Compile      
$ cd ~/ros2_ws  
$ ament build --only-packages sparse_bundle_adjustment  

For isolated build  
$ ament build --isolated --symlink-install --only sparse_bundle_adjustment  

## As libraries in other ROS 2 pkg  
Add "find_package(sparse_bundle_adjustment REQUIRED)" in your CMakeLists.txt   
