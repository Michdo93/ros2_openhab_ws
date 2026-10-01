#!/usr/bin/env python3
"""
string_subscriber.py
Static example: Subscriber for openHAB String items.
Subscribes to: /openhab/state/TestString
Usage:
    ros2 run openhab_static_examples string_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import StringState


class StringSubscriber(Node):
    def __init__(self):
        super().__init__("string_subscriber")
        self.subscription = self.create_subscription(
            StringState,
            "/openhab/state/TestString",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestString")

    def callback(self, msg: StringState):
        self.get_logger().info("[String] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = StringSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
