#!/usr/bin/env python3
"""
player_get_state_client.py
Static example: Service client to get the state of a Player item.
Calls service: /openhab/get_state/player
Usage:
    ros2 run openhab_static_examples player_get_state_client.py
"""

import rclpy
from rclpy.node import Node
from openhab_msgs.srv import GetPlayerState


ITEM_NAME = "TestPlayer"  # Change to your item name


class PlayerGetStateClient(Node):
    def __init__(self):
        super().__init__("player_get_state_client")
        self.client = self.create_client(GetPlayerState, "/openhab/get_state/player")
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /openhab/get_state/player service...")

    def send_request(self):
        request = GetPlayerState.Request()
        request.item_name = ITEM_NAME
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        if response.success:
            self.get_logger().info("[Player] State of " + ITEM_NAME + ":")
            self.get_logger().info("  state.state: " + str(getattr(getattr(response, "state", None), "state", "")))
        else:
            self.get_logger().error("Failed: " + response.message)


def main(args=None):
    rclpy.init(args=args)
    node = PlayerGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
