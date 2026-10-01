#!/usr/bin/env python3
"""
color_get_state_client.py
Static example: Service client to get the state of a Color item.
Calls service: /openhab/get_state/color
Usage:
    ros2 run openhab_static_examples color_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetColorState


ITEM_NAME = "TestColor"  # Change to your item name


class ColorGetStateClient(Node):
    def __init__(self):
        super().__init__("color_get_state_client")
        self.client = self.create_client(GetColorState, "/openhab/get_state/color")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/color service...")

    def send_request(self):
        request = GetColorState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Color] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
            self.get_logger().info("  state.hue: " + str(getattr(getattr(response, "state", None), "hue", "")))
            self.get_logger().info("  state.saturation: " + str(getattr(getattr(response, "state", None), "saturation", "")))
            self.get_logger().info("  state.brightness: " + str(getattr(getattr(response, "state", None), "brightness", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = ColorGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
