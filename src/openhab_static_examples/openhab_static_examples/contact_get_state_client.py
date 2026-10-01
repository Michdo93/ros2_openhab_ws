#!/usr/bin/env python3
"""
contact_get_state_client.py
Static example: Service client to get the state of a Contact item.
Calls service: /openhab/get_state/contact
Usage:
    ros2 run openhab_static_examples contact_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetContactState


ITEM_NAME = "TestContact"  # Change to your item name


class ContactGetStateClient(Node):
    def __init__(self):
        super().__init__("contact_get_state_client")
        self.client = self.create_client(GetContactState, "/openhab/get_state/contact")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/contact service...")

    def send_request(self):
        request = GetContactState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Contact] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = ContactGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
