#!/usr/bin/env python3
"""
joy2twist_node.py — Logitech F710 → ROS 2 Twist publisher

This is a packaged variant for ROS 2 (ament_python). By default this node
publishes joystick-derived Twist messages to `/cmd_vel_joy` so you can
connect it as an input to `twist_mux` (which arbitrates multiple Twist sources
and outputs to `/cmd_vel`). The output topic is configurable via the
`output_topic` node parameter.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import ParameterDescriptor, FloatingPointRange


# Axes/buttons defaults (Logitech F710 XInput)
AXIS_LINEAR_X = 1
AXIS_LINEAR_Y = 0
AXIS_ANGULAR_Z = 3
AXIS_RT = 5
BTN_LB = 4
BTN_RB = 5
DEAD_ZONE = 0.08


class Joy2Twist(Node):
    def __init__(self):
        super().__init__('joy2twist')

        float_desc = lambda desc: ParameterDescriptor(description=desc,
            floating_point_range=[FloatingPointRange(from_value=0.0, to_value=10.0, step=0.0)])

        # Velocity factors
        self.declare_parameter('linear_velocity_factor.fast', 1.0, float_desc('Fast linear speed'))
        self.declare_parameter('linear_velocity_factor.regular', 0.5, float_desc('Regular linear speed'))
        self.declare_parameter('linear_velocity_factor.slow', 0.2, float_desc('Slow linear speed'))

        self.declare_parameter('angular_velocity_factor.fast', 1.0, float_desc('Fast angular speed'))
        self.declare_parameter('angular_velocity_factor.regular', 0.5, float_desc('Regular angular speed'))
        self.declare_parameter('angular_velocity_factor.slow', 0.2, float_desc('Slow angular speed'))

        # Index mappings (override in YAML if needed)
        self.declare_parameter('button_index_map.axis.linear_x', AXIS_LINEAR_X)
        self.declare_parameter('button_index_map.axis.linear_y', AXIS_LINEAR_Y)
        self.declare_parameter('button_index_map.axis.angular_z', AXIS_ANGULAR_Z)
        self.declare_parameter('button_index_map.dead_man_switch', BTN_LB)
        self.declare_parameter('button_index_map.fast_mode', BTN_RB)
        self.declare_parameter('button_index_map.slow_mode', BTN_RB)

        # Output topic (default publishes to /cmd_vel_joy so twist_mux can consume it)
        self.declare_parameter('output_topic', '/cmd_vel_joy')

        out_topic = self.get_parameter('output_topic').value
        self._pub = self.create_publisher(Twist, out_topic, 10)
        self._sub = self.create_subscription(Joy, '/joy', self._joy_cb, 10)

        self.get_logger().info(f'joy2twist ready. publishing to: {out_topic}')

    def _p(self, name):
        return self.get_parameter(name).value

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

    def _vel_factors(self, joy: Joy):
        dead_man_idx = self._p('button_index_map.dead_man_switch')
        slow_idx = self._p('button_index_map.slow_mode')
        fast_idx = self._p('button_index_map.fast_mode')

        # If dead-man not held -> zero
        if not self._btn(joy, dead_man_idx):
            return 0.0, 0.0

        # Fast: using RT axis (if provided) or fast button
        rt_val = joy.axes[AXIS_RT] if AXIS_RT < len(joy.axes) else -1.0
        rt_norm = (rt_val + 1.0) / 2.0
        if rt_norm > 0.5 or self._btn(joy, fast_idx):
            return (self._p('linear_velocity_factor.fast'), self._p('angular_velocity_factor.fast'))

        if self._btn(joy, slow_idx):
            return (self._p('linear_velocity_factor.slow'), self._p('angular_velocity_factor.slow'))

        return (self._p('linear_velocity_factor.regular'), self._p('angular_velocity_factor.regular'))

    def _joy_cb(self, joy: Joy):
        lin_factor, ang_factor = self._vel_factors(joy)

        ax_lx = self._p('button_index_map.axis.linear_x')
        ax_ly = self._p('button_index_map.axis.linear_y')
        ax_az = self._p('button_index_map.axis.angular_z')

        twist = Twist()

        if lin_factor == 0.0:
            self._pub.publish(twist)
            return

        twist.linear.x = -self._axis(joy, ax_lx) * lin_factor
        twist.linear.y = self._axis(joy, ax_ly) * lin_factor
        twist.angular.z = self._axis(joy, ax_az) * ang_factor

        self._pub.publish(twist)


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


if __name__ == '__main__':
    main()
