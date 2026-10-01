#!/usr/bin/env python3
"""
call_subscriber.py
Static example: Subscriber for openHAB Call items.
Subscribes to: /openhab/state/TestCall
Usage:
    ros2 run openhab_static_examples call_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import CallState


class CallSubscriber(Node):
    def __init__(self):
        super().__init__("call_subscriber")
        self.subscription = self.create_subscription(
            CallState,
            "/openhab/state/TestCall",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestCall")

    def callback(self, msg: CallState):
        self.get_logger().info("[Call] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = CallSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
