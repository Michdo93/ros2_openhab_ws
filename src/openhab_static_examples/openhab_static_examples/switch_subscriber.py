#!/usr/bin/env python3
"""
switch_subscriber.py
Static example: Subscriber for openHAB Switch items.
Subscribes to: /openhab/state/TestSwitch
Usage:
    ros2 run openhab_static_examples switch_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import SwitchState


class SwitchSubscriber(Node):
    def __init__(self):
        super().__init__("switch_subscriber")
        self.subscription = self.create_subscription(
            SwitchState,
            "/openhab/state/TestSwitch",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestSwitch")

    def callback(self, msg: SwitchState):
        self.get_logger().info("[Switch] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = SwitchSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
