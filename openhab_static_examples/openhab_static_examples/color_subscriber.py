#!/usr/bin/env python3
"""
color_subscriber.py
Static example: Subscriber for openHAB Color items.
Subscribes to: /openhab/state/TestColor
Usage:
    ros2 run openhab_static_examples color_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import ColorState


class ColorSubscriber(Node):
    def __init__(self):
        super().__init__("color_subscriber")
        self.subscription = self.create_subscription(
            ColorState,
            "/openhab/state/TestColor",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestColor")

    def callback(self, msg: ColorState):
        self.get_logger().info("[Color] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))
        self.get_logger().info("  hue: " + str(msg.hue))
        self.get_logger().info("  saturation: " + str(msg.saturation))
        self.get_logger().info("  brightness: " + str(msg.brightness))


def main(args=None):
    rclpy.init(args=args)
    node = ColorSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
