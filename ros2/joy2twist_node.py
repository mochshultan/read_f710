#!/usr/bin/env python3
"""
joy2twist_node.py — Logitech F710 → ROS 2 Twist publisher
============================================================
Converts sensor_msgs/Joy (from the `joy` ROS2 node) into
geometry_msgs/Twist on /cmd_vel.

Button mapping (XInput mode, switch set to 'X'):
  LB  (button 4) — Dead-man switch: MUST be held to send velocity
  RB  (button 5) — Slow mode   (factor 0.2 of max)
  RT  (axis 5)   — Fast mode   (factor 1.0 of max, threshold > 0.5)
  Default speed  — Regular mode (factor 0.5 of max)

Axes (XInput):
  Left stick  Y (axis 1) → linear.x   (forward/back)
  Left stick  X (axis 0) → linear.y   (strafe, omni robots only)
  Right stick X (axis 3) → angular.z  (rotation)

Reference:
  https://husarion.com/tutorials/ros-equipment/gamepad-f710/
  https://github.com/husarion/joy2twist/tree/ros2
  http://wiki.ros.org/joy#Logitech_Wireless_Gamepad_F710_.28XInput_Mode.29

Usage:
  # Install deps
  pip install rclpy

  # In your ROS 2 workspace:
  ros2 run <your_package> joy2twist_node

  # Or directly:
  python3 joy2twist_node.py

  # The joy node must also be running:
  ros2 run joy joy_node
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import ParameterDescriptor, FloatingPointRange


# ─────────────────────────────────────────────────────────────────────────────
# Default XInput mapping constants (Logitech F710, switch set to 'X')
# ─────────────────────────────────────────────────────────────────────────────

# Axes
AXIS_LINEAR_X  = 1   # Left stick  Y  (push forward  = positive)
AXIS_LINEAR_Y  = 0   # Left stick  X  (push left     = positive; omni only)
AXIS_ANGULAR_Z = 3   # Right stick X  (push left     = positive rotation)
AXIS_LT        = 2   # Left trigger  (idle = -1, full = +1) — unused by default
AXIS_RT        = 5   # Right trigger (idle = -1, full = +1) — fast mode

# Buttons
BTN_A      = 0
BTN_B      = 1
BTN_X      = 2
BTN_Y      = 3
BTN_LB     = 4   # Dead-man switch — must be held to publish velocity
BTN_RB     = 5   # Slow mode
BTN_BACK   = 6
BTN_START  = 7
BTN_L3     = 8
BTN_R3     = 9

DEAD_ZONE  = 0.08   # Ignore stick noise below this threshold


class Joy2Twist(Node):
    """ROS 2 node: sensor_msgs/Joy → geometry_msgs/Twist."""

    def __init__(self):
        super().__init__("joy2twist")

        # ── Declare parameters (overridable via YAML or CLI) ───────────────
        float_desc = lambda desc: ParameterDescriptor(description=desc,
            floating_point_range=[FloatingPointRange(from_value=0.0, to_value=10.0, step=0.0)])

        self.declare_parameter("linear_velocity_factor.fast",    1.0, float_desc("Fast linear speed [m/s]"))
        self.declare_parameter("linear_velocity_factor.regular", 0.5, float_desc("Regular linear speed [m/s]"))
        self.declare_parameter("linear_velocity_factor.slow",    0.2, float_desc("Slow linear speed [m/s]"))

        self.declare_parameter("angular_velocity_factor.fast",    1.0, float_desc("Fast angular speed [rad/s]"))
        self.declare_parameter("angular_velocity_factor.regular", 0.5, float_desc("Regular angular speed [rad/s]"))
        self.declare_parameter("angular_velocity_factor.slow",    0.2, float_desc("Slow angular speed [rad/s]"))

        self.declare_parameter("button_index_map.axis.linear_x",  AXIS_LINEAR_X,
                               ParameterDescriptor(description="Axis index for linear X"))
        self.declare_parameter("button_index_map.axis.linear_y",  AXIS_LINEAR_Y,
                               ParameterDescriptor(description="Axis index for linear Y"))
        self.declare_parameter("button_index_map.axis.angular_z", AXIS_ANGULAR_Z,
                               ParameterDescriptor(description="Axis index for angular Z"))
        self.declare_parameter("button_index_map.dead_man_switch", BTN_LB,
                               ParameterDescriptor(description="Button index for dead-man switch (LB)"))
        self.declare_parameter("button_index_map.fast_mode",  BTN_START,
                               ParameterDescriptor(description="Axis/button index for fast mode (RT)"))
        self.declare_parameter("button_index_map.slow_mode",  BTN_RB,
                               ParameterDescriptor(description="Button index for slow mode (RB)"))

        # ── QoS and pub/sub ────────────────────────────────────────────────
        self._pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self._sub = self.create_subscription(Joy, "/joy", self._joy_cb, 10)

        self.get_logger().info(
            "joy2twist ready.\n"
            "  LB (btn 4) = dead-man switch  |  RB (btn 5) = slow  |  RT (axis 5) = fast\n"
            "  Left stick = linear x/y  |  Right stick X = angular z"
        )

    # ── Parameter helpers ──────────────────────────────────────────────────

    def _p(self, name):
        return self.get_parameter(name).value

    def _vel_factors(self, joy: Joy):
        """Return (linear_factor, angular_factor) based on held buttons."""
        dead_man_idx = self._p("button_index_map.dead_man_switch")
        slow_idx     = self._p("button_index_map.slow_mode")
        rt_axis      = AXIS_RT   # Fast mode comes from RT trigger (analog)

        # Safety: if dead-man switch not held, stop
        if not self._btn(joy, dead_man_idx):
            return 0.0, 0.0

        # RT > 0.5 → fast
        rt_val = joy.axes[rt_axis] if rt_axis < len(joy.axes) else -1.0
        rt_norm = (rt_val + 1.0) / 2.0   # -1..+1 → 0..1
        if rt_norm > 0.5:
            return (self._p("linear_velocity_factor.fast"),
                    self._p("angular_velocity_factor.fast"))

        # RB → slow
        if self._btn(joy, slow_idx):
            return (self._p("linear_velocity_factor.slow"),
                    self._p("angular_velocity_factor.slow"))

        # Default: regular
        return (self._p("linear_velocity_factor.regular"),
                self._p("angular_velocity_factor.regular"))

    @staticmethod
    def _btn(joy: Joy, idx: int) -> bool:
        if idx < 0 or idx >= len(joy.buttons):
            return False
        return bool(joy.buttons[idx])

    @staticmethod
    def _axis(joy: Joy, idx: int, dead: float = DEAD_ZONE) -> float:
        if idx < 0 or idx >= len(joy.axes):
            return 0.0
        v = joy.axes[idx]
        return 0.0 if abs(v) < dead else float(v)

    # ── Callback ───────────────────────────────────────────────────────────

    def _joy_cb(self, joy: Joy):
        lin_factor, ang_factor = self._vel_factors(joy)

        ax_lx  = self._p("button_index_map.axis.linear_x")
        ax_ly  = self._p("button_index_map.axis.linear_y")
        ax_az  = self._p("button_index_map.axis.angular_z")

        twist = Twist()

        if lin_factor == 0.0:
            # Dead-man switch released — publish zero once, then nothing
            self._pub.publish(twist)
            return

        # Positive Y on left stick = forward (ROS convention: +x = forward)
        # Note: pygame and ROS joy both invert stick Y (-1 = up/forward in hardware)
        twist.linear.x  = -self._axis(joy, ax_lx)  * lin_factor   # fwd/back
        twist.linear.y  =  self._axis(joy, ax_ly)  * lin_factor   # strafe (omni)
        twist.angular.z =  self._axis(joy, ax_az)  * ang_factor   # rotation

        self._pub.publish(twist)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = Joy2Twist()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
