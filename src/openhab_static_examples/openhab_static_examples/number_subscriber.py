#!/usr/bin/env python3
"""
number_subscriber.py
Static example: Subscriber for openHAB Number items.
Subscribes to: /openhab/state/TestNumber
Usage:
    ros2 run openhab_static_examples number_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import NumberState


class NumberSubscriber(Node):
    def __init__(self):
        super().__init__("number_subscriber")
        self.subscription = self.create_subscription(
            NumberState,
            "/openhab/state/TestNumber",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestNumber")

    def callback(self, msg: NumberState):
        self.get_logger().info("[Number] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))
        self.get_logger().info("  unit: " + str(msg.unit))


def main(args=None):
    rclpy.init(args=args)
    node = NumberSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
