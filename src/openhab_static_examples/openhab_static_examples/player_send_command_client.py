#!/usr/bin/env python3
"""
player_send_command_client.py
Static example: Service client to send a command to a Player item.
Calls service: /openhab/send_command/player
Usage:
    ros2 run openhab_static_examples player_send_command_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import SendPlayerCommand


ITEM_NAME = "TestPlayer"  # Change to your item name
COMMAND   = "PLAY"  # PLAY, PAUSE, NEXT, PREVIOUS, REWIND, FASTFORWARD


class PlayerSendCommandClient(Node):
    def __init__(self):
        super().__init__("player_send_command_client")
        self.client = self.create_client(SendPlayerCommand, "/openhab/send_command/player")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/send_command/player service...")

    def send_command(self):
        request = SendPlayerCommand.Request()
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
    node = PlayerSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
