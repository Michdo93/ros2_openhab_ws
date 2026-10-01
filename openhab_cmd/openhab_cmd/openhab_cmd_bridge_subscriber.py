#!/usr/bin/env python3
"""
openhab_cmd_bridge_subscriber.py
=================================
Bridge subscriber: subscribes to /openhab/command/<item_name> and
forwards every received command to the openHAB REST API via sendCommand.

This is the "sink" counterpart to openhab_publisher.py.
Together they form the push pipeline:

    [Your ROS2 node]
         │ publishes openhab_msgs/msg/*Command
         ▼
    /openhab/command/<ItemName>
         │
         ▼
    [openhab_cmd_bridge_subscriber]
         │ calls Items.sendCommand() via REST
         ▼
    [openHAB server]

Parameters (--ros-args -p):
    item_name      (string,  required) – item to subscribe + control
    item_type      (string,  default: "Switch") – message type to expect
    openhab_url    (string,  default: "http://127.0.0.1:8080")
    openhab_token  (string,  default: "")
    openhab_user   (string,  default: "openhab")
    openhab_password (string,default: "habopen")

Usage:
    ros2 run openhab_cmd openhab_cmd_bridge_subscriber.py \
        --ros-args -p item_name:=LivingRoomLight \
                   -p item_type:=Switch \
                   -p openhab_url:=http://192.168.1.100:8080 \
                   -p openhab_token:=oh.openhab.xxxx
"""

import rclpy
from rclpy.node import Node

from openhab_msgs.msg import (
    ColorCommand, ContactCommand, DateTimeCommand, DimmerCommand,
    LocationCommand, NumberCommand, PlayerCommand, RollershutterCommand,
    StringCommand, SwitchCommand,
)

try:
    from openhab import OpenHABClient, Items
    OPENHAB_AVAILABLE = True
except ImportError:
    OPENHAB_AVAILABLE = False

CMD_MSG_MAP = {
    "Color":         ColorCommand,
    "Contact":       ContactCommand,
    "DateTime":      DateTimeCommand,
    "Dimmer":        DimmerCommand,
    "Location":      LocationCommand,
    "Number":        NumberCommand,
    "Player":        PlayerCommand,
    "Rollershutter": RollershutterCommand,
    "String":        StringCommand,
    "Switch":        SwitchCommand,
}


def _msg_to_command_str(item_type: str, msg) -> str:
    """Convert a Command message back to the openHAB command string."""
    if item_type == "Switch":
        return msg.command
    if item_type == "Dimmer":
        if msg.command_type in ("ON", "OFF", "INCREASE", "DECREASE", "REFRESH"):
            return msg.command_type
        return str(msg.percent)
    if item_type == "Color":
        if msg.command_type in ("ON", "OFF", "INCREASE", "DECREASE", "REFRESH"):
            return msg.command_type
        return f"{msg.hue},{msg.saturation},{msg.brightness}"
    if item_type == "Contact":
        return msg.command
    if item_type == "DateTime":
        return msg.command
    if item_type == "Location":
        return f"{msg.latitude},{msg.longitude},{msg.altitude}"
    if item_type == "Number":
        if msg.unit:
            return f"{msg.value} {msg.unit}"
        return str(msg.value)
    if item_type == "Player":
        return msg.command
    if item_type == "Rollershutter":
        if msg.command_type in ("UP", "DOWN", "STOP", "MOVE", "REFRESH"):
            return msg.command_type
        return str(msg.percent)
    if item_type == "String":
        return msg.command
    return str(getattr(msg, "command", ""))


class OpenHABCmdBridgeSubscriber(Node):
    def __init__(self):
        super().__init__("openhab_cmd_bridge_subscriber")

        self.declare_parameter("item_name",       "")
        self.declare_parameter("item_type",       "Switch")
        self.declare_parameter("openhab_url",     "http://127.0.0.1:8080")
        self.declare_parameter("openhab_token",   "")
        self.declare_parameter("openhab_user",    "openhab")
        self.declare_parameter("openhab_password","habopen")

        item_name = self.get_parameter("item_name").get_parameter_value().string_value
        item_type = self.get_parameter("item_type").get_parameter_value().string_value
        url       = self.get_parameter("openhab_url").get_parameter_value().string_value
        token     = self.get_parameter("openhab_token").get_parameter_value().string_value
        user      = self.get_parameter("openhab_user").get_parameter_value().string_value
        password  = self.get_parameter("openhab_password").get_parameter_value().string_value

        if not item_name:
            self.get_logger().error("Parameter 'item_name' is required!")
            return

        if item_type not in CMD_MSG_MAP:
            self.get_logger().warn(
                f"Unknown item_type '{item_type}', falling back to 'String'."
            )
            item_type = "String"

        self._item_type = item_type

        # Setup REST client
        if not OPENHAB_AVAILABLE:
            self.get_logger().error(
                "python-openhab-rest-client not installed! "
                "Run: pip install python-openhab-rest-client"
            )
            self._items = None
        else:
            if token:
                client = OpenHABClient(url=url, token=token)
            else:
                client = OpenHABClient(url=url, username=user, password=password)
            self._items = Items(client)

        msg_class = CMD_MSG_MAP[item_type]
        topic = f"/openhab/command/{item_name}"

        self.subscription = self.create_subscription(
            msg_class,
            topic,
            self._callback,
            10,
        )
        self.get_logger().info(
            f"Bridge subscriber listening on {topic} → openHAB REST"
        )

    def _callback(self, msg):
        if self._items is None:
            self.get_logger().error("openHAB client not available!")
            return
        try:
            command_str = _msg_to_command_str(self._item_type, msg)
            self._items.sendCommand(msg.item_name, command_str)
            self.get_logger().info(
                f"Sent command '{command_str}' to '{msg.item_name}'"
            )
        except Exception as e:
            self.get_logger().error(f"sendCommand failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABCmdBridgeSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
