#!/usr/bin/env python3
"""
rollershutter_get_state_client.py
Static example: Service client to get the state of a Rollershutter item.
Calls service: /openhab/get_state/rollershutter
Usage:
    ros2 run openhab_static_examples rollershutter_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetRollershutterState


ITEM_NAME = "TestRollershutter"  # Change to your item name


class RollershutterGetStateClient(Node):
    def __init__(self):
        super().__init__("rollershutter_get_state_client")
        self.client = self.create_client(GetRollershutterState, "/openhab/get_state/rollershutter")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/rollershutter service...")

    def send_request(self):
        request = GetRollershutterState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Rollershutter] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = RollershutterGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
