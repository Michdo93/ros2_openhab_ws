#!/usr/bin/env python3
"""
datetime_get_state_client.py
Static example: Service client to get the state of a DateTime item.
Calls service: /openhab/get_state/datetime
Usage:
    ros2 run openhab_static_examples datetime_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetDateTimeState


ITEM_NAME = "TestDateTime"  # Change to your item name


class DateTimeGetStateClient(Node):
    def __init__(self):
        super().__init__("datetime_get_state_client")
        self.client = self.create_client(GetDateTimeState, "/openhab/get_state/datetime")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/datetime service...")

    def send_request(self):
        request = GetDateTimeState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[DateTime] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = DateTimeGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
