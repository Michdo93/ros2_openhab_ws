#!/usr/bin/env python3
"""
dimmer_send_command_client.py
Static example: Service client to send a command to a Dimmer item.
Calls service: /openhab/send_command/dimmer
Usage:
    ros2 run openhab_static_examples dimmer_send_command_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import SendDimmerCommand


ITEM_NAME = "TestDimmer"  # Change to your item name
COMMAND   = "75"  # 0-100, ON, OFF, INCREASE, DECREASE, REFRESH


class DimmerSendCommandClient(Node):
    def __init__(self):
        super().__init__("dimmer_send_command_client")
        self.client = self.create_client(SendDimmerCommand, "/openhab/send_command/dimmer")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/send_command/dimmer service...")

    def send_command(self):
        request = SendDimmerCommand.Request()
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
    node = DimmerSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
