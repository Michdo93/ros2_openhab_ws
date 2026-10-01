#!/usr/bin/env python3
"""
rollershutter_subscriber.py
Static example: Subscriber for openHAB Rollershutter items.
Subscribes to: /openhab/state/TestRollershutter
Usage:
    ros2 run openhab_static_examples rollershutter_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import RollershutterState


class RollershutterSubscriber(Node):
    def __init__(self):
        super().__init__("rollershutter_subscriber")
        self.subscription = self.create_subscription(
            RollershutterState,
            "/openhab/state/TestRollershutter",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestRollershutter")

    def callback(self, msg: RollershutterState):
        self.get_logger().info("[Rollershutter] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = RollershutterSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
