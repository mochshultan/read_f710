from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='f710_joy2twist',
            executable='joy2twist_node',
            name='joy2twist',
            output='screen',
            parameters=[{'output_topic': '/cmd_vel_joy'}]
        )
    ])
