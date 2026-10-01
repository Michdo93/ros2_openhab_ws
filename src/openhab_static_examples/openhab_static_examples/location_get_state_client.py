#!/usr/bin/env python3
"""
location_get_state_client.py
Static example: Service client to get the state of a Location item.
Calls service: /openhab/get_state/location
Usage:
    ros2 run openhab_static_examples location_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetLocationState


ITEM_NAME = "TestLocation"  # Change to your item name


class LocationGetStateClient(Node):
    def __init__(self):
        super().__init__("location_get_state_client")
        self.client = self.create_client(GetLocationState, "/openhab/get_state/location")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/location service...")

    def send_request(self):
        request = GetLocationState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Location] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
            self.get_logger().info("  state.latitude: " + str(getattr(getattr(response, "state", None), "latitude", "")))
            self.get_logger().info("  state.longitude: " + str(getattr(getattr(response, "state", None), "longitude", "")))
            self.get_logger().info("  state.altitude: " + str(getattr(getattr(response, "state", None), "altitude", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = LocationGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
