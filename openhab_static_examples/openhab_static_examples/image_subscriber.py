#!/usr/bin/env python3
"""
image_subscriber.py
Static example: Subscriber for openHAB Image items.
Subscribes to: /openhab/state/TestImage
Usage:
    ros2 run openhab_static_examples image_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import ImageState


class ImageSubscriber(Node):
    def __init__(self):
        super().__init__("image_subscriber")
        self.subscription = self.create_subscription(
            ImageState,
            "/openhab/state/TestImage",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestImage")

    def callback(self, msg: ImageState):
        self.get_logger().info("[Image] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = ImageSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
