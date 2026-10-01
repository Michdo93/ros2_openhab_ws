#!/usr/bin/env python3
"""
datetime_send_command_client.py
Static example: Service client to send a command to a DateTime item.
Calls service: /openhab/send_command/datetime
Usage:
    ros2 run openhab_static_examples datetime_send_command_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import SendDateTimeCommand


ITEM_NAME = "TestDateTime"  # Change to your item name
COMMAND   = "2024-06-01T12:00:00.000+0000"  # ISO 8601 datetime


class DateTimeSendCommandClient(Node):
    def __init__(self):
        super().__init__("datetime_send_command_client")
        self.client = self.create_client(SendDateTimeCommand, "/openhab/send_command/datetime")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/send_command/datetime service...")

    def send_command(self):
        request = SendDateTimeCommand.Request()
        request.item_name = ITEM_NAME
        request.command   = COMMAND
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("OK: " + response.message)
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = DateTimeSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
