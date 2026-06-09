# f710_joy2twist

Minimal ROS 2 (Humble) ament_python package that converts `sensor_msgs/Joy`
into `geometry_msgs/Twist`. By default the node publishes to `/cmd_vel_joy`
so you can include it as an input to `twist_mux` and let the mux publish the
final `/cmd_vel` used by your robot.

Build & install (on a machine with ROS 2 Humble):

```
cd <your_ros2_ws>/src
cp -r /path/to/f710/ros2 .
cd ..
colcon build --packages-select f710_joy2twist
source install/setup.bash
ros2 launch f710_joy2twist joy2twist_launch.py
```

To use with `twist_mux`:

- Add the `config/twist_mux.yaml` entries to your `twist_mux` configuration,
  or include `/cmd_vel_joy` as an input topic with appropriate priority.

Note: this workspace is prepared for ROS 2 on Linux; there is no ROS2 on
Windows by default — you can still inspect the code here and build it on a
Linux machine or WSL2 with ROS 2 Humble installed.
