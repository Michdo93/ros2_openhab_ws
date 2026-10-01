#!/usr/bin/env python3
"""
number_get_state_client.py
Static example: Service client to get the state of a Number item.
Calls service: /openhab/get_state/number
Usage:
    ros2 run openhab_static_examples number_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetNumberState


ITEM_NAME = "TestNumber"  # Change to your item name


class NumberGetStateClient(Node):
    def __init__(self):
        super().__init__("number_get_state_client")
        self.client = self.create_client(GetNumberState, "/openhab/get_state/number")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/number service...")

    def send_request(self):
        request = GetNumberState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Number] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
            self.get_logger().info("  state.unit: " + str(getattr(getattr(response, "state", None), "unit", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = NumberGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
