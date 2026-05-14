
VOXEL_SIZE = 0.05
include "transform.lua"

options = {
  tracking_frame = "base_footprint",
  pipeline = {
    {
      action = "min_max_range_filter",
      min_range = 0.5,
      max_range = 50.0,
    },
    {
      action = "voxel_filter_and_remove_moving_objects",
      voxel_size = VOXEL_SIZE,
    },
    {
      action = "write_ply",
     filename = "turtlebot_house_3d.ply",
    },
  }
}
return options
