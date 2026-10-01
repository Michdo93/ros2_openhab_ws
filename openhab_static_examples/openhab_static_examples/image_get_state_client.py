#!/usr/bin/env python3
"""
image_get_state_client.py
Static example: Service client to get the state of a Image item.
Calls service: /openhab/get_state/image
Usage:
    ros2 run openhab_static_examples image_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetImageState


ITEM_NAME = "TestImage"  # Change to your item name


class ImageGetStateClient(Node):
    def __init__(self):
        super().__init__("image_get_state_client")
        self.client = self.create_client(GetImageState, "/openhab/get_state/image")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/image service...")

    def send_request(self):
        request = GetImageState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Image] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = ImageGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
