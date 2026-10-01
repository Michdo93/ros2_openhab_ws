#!/usr/bin/env python3
"""
player_subscriber.py
Static example: Subscriber for openHAB Player items.
Subscribes to: /openhab/state/TestPlayer
Usage:
    ros2 run openhab_static_examples player_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import PlayerState


class PlayerSubscriber(Node):
    def __init__(self):
        super().__init__("player_subscriber")
        self.subscription = self.create_subscription(
            PlayerState,
            "/openhab/state/TestPlayer",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestPlayer")

    def callback(self, msg: PlayerState):
        self.get_logger().info("[Player] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))


def main(args=None):
    rclpy.init(args=args)
    node = PlayerSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
