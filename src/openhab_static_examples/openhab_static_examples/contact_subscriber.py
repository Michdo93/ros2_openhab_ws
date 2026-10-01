#!/usr/bin/env python3
"""
contact_subscriber.py
Static example: Subscriber for openHAB Contact items.
Subscribes to: /openhab/state/TestContact
Usage:
    ros2 run openhab_static_examples contact_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import ContactState


class ContactSubscriber(Node):
    def __init__(self):
        super().__init__("contact_subscriber")
        self.subscription = self.create_subscription(
            ContactState,
            "/openhab/state/TestContact",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestContact")

    def callback(self, msg: ContactState):
        self.get_logger().info("[Contact] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = ContactSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
