#!/usr/bin/env python3
"""
dimmer_subscriber.py
Static example: Subscriber for openHAB Dimmer items.
Subscribes to: /openhab/state/TestDimmer
Usage:
    ros2 run openhab_static_examples dimmer_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import DimmerState


class DimmerSubscriber(Node):
    def __init__(self):
        super().__init__("dimmer_subscriber")
        self.subscription = self.create_subscription(
            DimmerState,
            "/openhab/state/TestDimmer",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestDimmer")

    def callback(self, msg: DimmerState):
        self.get_logger().info("[Dimmer] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = DimmerSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
