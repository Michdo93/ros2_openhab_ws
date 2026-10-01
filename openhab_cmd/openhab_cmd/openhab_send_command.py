#!/usr/bin/env python3
"""
openhab_send_command.py
=======================
Generic service client: send a command to ANY openHAB item.
Item name, item type and command are passed as ROS2 node parameters.

Parameters (--ros-args -p):
    item_name  (string, required) – openHAB item name
    item_type  (string, default: "Switch") – one of:
               Color, Contact, DateTime, Dimmer, Location, Number,
               Player, Rollershutter, String, Switch
    command    (string, required) – command to send

Usage:
    # Turn a Switch ON
    ros2 run openhab_cmd openhab_send_command.py \
        --ros-args -p item_name:=LivingRoomLight \
                   -p item_type:=Switch \
                   -p command:=ON

    # Set a Dimmer to 75%
    ros2 run openhab_cmd openhab_send_command.py \
        --ros-args -p item_name:=LivingRoomDimmer \
                   -p item_type:=Dimmer \
                   -p command:=75

    # Set a Color item (HSB)
    ros2 run openhab_cmd openhab_send_command.py \
        --ros-args -p item_name:=LivingRoomColor \
                   -p item_type:=Color \
                   -p command:="120.0,100.0,100.0"

    # Set a Rollershutter position
    ros2 run openhab_cmd openhab_send_command.py \
        --ros-args -p item_name:=BedroomBlind \
                   -p item_type:=Rollershutter \
                   -p command:=UP

    # Send a GPS location
    ros2 run openhab_cmd openhab_send_command.py \
        --ros-args -p item_name:=MyLocation \
                   -p item_type:=Location \
                   -p command:="48.858,2.294,35.0"
"""

import rclpy
from rclpy.node import Node

from openhab_msgs.srv import (
    SendColorCommand, SendContactCommand, SendDateTimeCommand,
    SendDimmerCommand, SendLocationCommand, SendNumberCommand,
    SendPlayerCommand, SendRollershutterCommand, SendStringCommand,
    SendSwitchCommand,
)

SERVICE_MAP = {
    "Color":         (SendColorCommand,         "/openhab/send_command/color"),
    "Contact":       (SendContactCommand,       "/openhab/send_command/contact"),
    "DateTime":      (SendDateTimeCommand,      "/openhab/send_command/datetime"),
    "Dimmer":        (SendDimmerCommand,        "/openhab/send_command/dimmer"),
    "Location":      (SendLocationCommand,      "/openhab/send_command/location"),
    "Number":        (SendNumberCommand,        "/openhab/send_command/number"),
    "Player":        (SendPlayerCommand,        "/openhab/send_command/player"),
    "Rollershutter": (SendRollershutterCommand, "/openhab/send_command/rollershutter"),
    "String":        (SendStringCommand,        "/openhab/send_command/string"),
    "Switch":        (SendSwitchCommand,        "/openhab/send_command/switch"),
}


class OpenHABSendCommandClient(Node):
    def __init__(self):
        super().__init__("openhab_send_command")

        self.declare_parameter("item_name", "")
        self.declare_parameter("item_type", "Switch")
        self.declare_parameter("command",   "")

        self.item_name = self.get_parameter("item_name").get_parameter_value().string_value
        self.item_type = self.get_parameter("item_type").get_parameter_value().string_value
        self.command   = self.get_parameter("command").get_parameter_value().string_value

        if not self.item_name:
            self.get_logger().error("Parameter 'item_name' is required!")
            return
        if not self.command:
            self.get_logger().error("Parameter 'command' is required!")
            return
        if self.item_type not in SERVICE_MAP:
            self.get_logger().error(
                f"Unknown item_type '{self.item_type}'. "
                f"Valid types: {list(SERVICE_MAP.keys())}"
            )
            return

        srv_class, srv_topic = SERVICE_MAP[self.item_type]
        self.client = self.create_client(srv_class, srv_topic)

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f"Waiting for {srv_topic} ...")

    def send_command(self):
        if not self.item_name or not self.command or self.item_type not in SERVICE_MAP:
            return

        srv_class, srv_topic = SERVICE_MAP[self.item_type]
        request = srv_class.Request()
        request.item_name = self.item_name
        request.command   = self.command

        self.get_logger().info(
            f"Sending command '{self.command}' to "
            f"'{self.item_name}' ({self.item_type}) ..."
        )

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()

        if response is None:
            self.get_logger().error("No response received!")
            return

        if response.success:
            self.get_logger().info(f"OK: {response.message}")
        else:
            self.get_logger().error(f"Failed: {response.message}")


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABSendCommandClient()
    node.send_command()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
