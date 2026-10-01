#!/usr/bin/env python3
"""
number_send_command_client.py
Static example: Service client to send a command to a Number item.
Calls service: /openhab/send_command/number
Usage:
    ros2 run openhab_static_examples number_send_command_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import SendNumberCommand


ITEM_NAME = "TestNumber"  # Change to your item name
COMMAND   = "23.5"  # decimal value, optionally with unit e.g. 23.5 C


class NumberSendCommandClient(Node):
    def __init__(self):
        super().__init__("number_send_command_client")
        self.client = self.create_client(SendNumberCommand, "/openhab/send_command/number")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/send_command/number service...")

    def send_command(self):
        request = SendNumberCommand.Request()
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
    node = NumberSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
