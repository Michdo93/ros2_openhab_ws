#!/usr/bin/env python3
"""
datetime_subscriber.py
Static example: Subscriber for openHAB DateTime items.
Subscribes to: /openhab/state/TestDateTime
Usage:
    ros2 run openhab_static_examples datetime_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import DateTimeState


class DateTimeSubscriber(Node):
    def __init__(self):
        super().__init__("datetime_subscriber")
        self.subscription = self.create_subscription(
            DateTimeState,
            "/openhab/state/TestDateTime",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestDateTime")

    def callback(self, msg: DateTimeState):
        self.get_logger().info("[DateTime] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = DateTimeSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
