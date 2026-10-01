#!/usr/bin/env python3
"""
contact_send_command_client.py
Static example: Service client to send a command to a Contact item.
Calls service: /openhab/send_command/contact
Usage:
    ros2 run openhab_static_examples contact_send_command_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import SendContactCommand


ITEM_NAME = "TestContact"  # Change to your item name
COMMAND   = "OPEN"  # OPEN, CLOSED, REFRESH


class ContactSendCommandClient(Node):
    def __init__(self):
        super().__init__("contact_send_command_client")
        self.client = self.create_client(SendContactCommand, "/openhab/send_command/contact")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/send_command/contact service...")

    def send_command(self):
        request = SendContactCommand.Request()
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
    node = ContactSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
