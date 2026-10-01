#!/usr/bin/env python3
"""
call_get_state_client.py
Static example: Service client to get the state of a Call item.
Calls service: /openhab/get_state/call
Usage:
    ros2 run openhab_static_examples call_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetCallState


ITEM_NAME = "TestCall"  # Change to your item name


class CallGetStateClient(Node):
    def __init__(self):
        super().__init__("call_get_state_client")
        self.client = self.create_client(GetCallState, "/openhab/get_state/call")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/call service...")

    def send_request(self):
        request = GetCallState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Call] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = CallGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
