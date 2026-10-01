#!/usr/bin/env python3
"""
switch_send_command_client.py
Static example: Service client to send a command to a Switch item.
Calls service: /openhab/send_command/switch
Usage:
    ros2 run openhab_static_examples switch_send_command_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import SendSwitchCommand


ITEM_NAME = "TestSwitch"  # Change to your item name
COMMAND   = "ON"  # ON, OFF, REFRESH


class SwitchSendCommandClient(Node):
    def __init__(self):
        super().__init__("switch_send_command_client")
        self.client = self.create_client(SendSwitchCommand, "/openhab/send_command/switch")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/send_command/switch service...")

    def send_command(self):
        request = SendSwitchCommand.Request()
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
    node = SwitchSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
