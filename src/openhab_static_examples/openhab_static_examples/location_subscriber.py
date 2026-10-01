#!/usr/bin/env python3
"""
location_subscriber.py
Static example: Subscriber for openHAB Location items.
Subscribes to: /openhab/state/TestLocation
Usage:
    ros2 run openhab_static_examples location_subscriber.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.msg import LocationState


class LocationSubscriber(Node):
    def __init__(self):
        super().__init__("location_subscriber")
        self.subscription = self.create_subscription(
            LocationState,
            "/openhab/state/TestLocation",
            self.callback,
            10,
        )
        self.get_logger().info("Subscribing to /openhab/state/TestLocation")

    def callback(self, msg: LocationState):
        self.get_logger().info("[Location] received from: " + msg.item_name)
        self.get_logger().info("  state: " + str(msg.state))
        self.get_logger().info("  latitude: " + str(msg.latitude))
        self.get_logger().info("  longitude: " + str(msg.longitude))
        self.get_logger().info("  altitude: " + str(msg.altitude))


def main(args=None):
    rclpy.init(args=args)
    node = LocationSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
