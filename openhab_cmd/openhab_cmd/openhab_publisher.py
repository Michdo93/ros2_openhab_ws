#!/usr/bin/env python3
"""
openhab_publisher.py
====================
Generic publisher: publish openHAB commands on the ROS2 command topic.
A matching subscriber (e.g. in openhab_cmd_subscriber or your own node)
subscribes to this topic and forwards the command to the openHAB REST API.

This node models the "I want to push data continuously from ROS2 into
openHAB" use case, where:
  - This node acts as the DATA SOURCE (publisher)
  - openhab_cmd_bridge_subscriber.py acts as the SINK (subscriber → REST)

Topic published:
    /openhab/command/<item_name>  →  openhab_msgs/msg/*Command

Parameters (--ros-args -p):
    item_name      (string,  required) – openHAB item name
    item_type      (string,  default: "Switch") – item type
    command        (string,  required) – command value to publish
    publish_once   (bool,    default: true)  – publish once then exit
    rate_hz        (double,  default: 1.0)   – publish rate if publish_once=false

Usage (one-shot):
    ros2 run openhab_cmd openhab_publisher.py \
        --ros-args -p item_name:=LivingRoomLight \
                   -p item_type:=Switch \
                   -p command:=ON

Usage (continuous at 0.5 Hz):
    ros2 run openhab_cmd openhab_publisher.py \
        --ros-args -p item_name:=LivingRoomDimmer \
                   -p item_type:=Dimmer \
                   -p command:=75 \
                   -p publish_once:=false \
                   -p rate_hz:=0.5
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header

from openhab_msgs.msg import (
    ColorCommand, ContactCommand, DateTimeCommand, DimmerCommand,
    LocationCommand, NumberCommand, PlayerCommand, RollershutterCommand,
    StringCommand, SwitchCommand,
)

# Map item_type → msg class
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


def _build_command_msg(node: Node, item_type: str, item_name: str, command: str):
    """Build the correct Command message for a given item type."""
    h = Header()
    h.stamp = node.get_clock().now().to_msg()
    h.frame_id = ""

    if item_type == "Switch":
        msg = SwitchCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "Dimmer":
        msg = DimmerCommand()
        msg.header = h; msg.item_name = item_name
        msg.command_type = command
        try:
            msg.percent = float(command)
        except ValueError:
            msg.percent = 0.0
        return msg

    if item_type == "Color":
        msg = ColorCommand()
        msg.header = h; msg.item_name = item_name
        msg.command_type = command
        try:
            parts = command.split(",")
            msg.hue = float(parts[0])
            msg.saturation = float(parts[1])
            msg.brightness = float(parts[2])
        except Exception:
            msg.hue = msg.saturation = msg.brightness = 0.0
        return msg

    if item_type == "Contact":
        msg = ContactCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "DateTime":
        msg = DateTimeCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "Location":
        msg = LocationCommand()
        msg.header = h; msg.item_name = item_name
        try:
            parts = command.split(",")
            msg.latitude  = float(parts[0])
            msg.longitude = float(parts[1])
            msg.altitude  = float(parts[2]) if len(parts) > 2 else 0.0
        except Exception:
            msg.latitude = msg.longitude = msg.altitude = 0.0
        return msg

    if item_type == "Number":
        msg = NumberCommand()
        msg.header = h; msg.item_name = item_name
        parts = command.split(" ", 1)
        try:
            msg.value = float(parts[0])
        except ValueError:
            msg.value = 0.0
        msg.unit = parts[1] if len(parts) > 1 else ""
        return msg

    if item_type == "Player":
        msg = PlayerCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "Rollershutter":
        msg = RollershutterCommand()
        msg.header = h; msg.item_name = item_name
        msg.command_type = command
        try:
            msg.percent = float(command)
        except ValueError:
            msg.percent = 0.0
        return msg

    if item_type == "Contact":
        msg = ContactCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "DateTime":
        msg = DateTimeCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "Player":
        msg = PlayerCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    if item_type == "String":
        msg = StringCommand()
        msg.header = h; msg.item_name = item_name; msg.command = command
        return msg

    # Fallback: StringCommand
    msg = StringCommand()
    msg.header = h; msg.item_name = item_name; msg.command = command
    return msg


class OpenHABCommandPublisher(Node):
    def __init__(self):
        super().__init__("openhab_publisher")

        self.declare_parameter("item_name",    "")
        self.declare_parameter("item_type",    "Switch")
        self.declare_parameter("command",      "")
        self.declare_parameter("publish_once", True)
        self.declare_parameter("rate_hz",      1.0)

        self._item_name    = self.get_parameter("item_name").get_parameter_value().string_value
        self._item_type    = self.get_parameter("item_type").get_parameter_value().string_value
        self._command      = self.get_parameter("command").get_parameter_value().string_value
        self._publish_once = self.get_parameter("publish_once").get_parameter_value().bool_value
        self._rate_hz      = self.get_parameter("rate_hz").get_parameter_value().double_value

        if not self._item_name:
            self.get_logger().error("Parameter 'item_name' is required!")
            return
        if not self._command:
            self.get_logger().error("Parameter 'command' is required!")
            return
        if self._item_type not in CMD_MSG_MAP:
            self.get_logger().warn(
                f"Unknown item_type '{self._item_type}', falling back to 'String'."
            )
            self._item_type = "String"

        msg_class = CMD_MSG_MAP[self._item_type]
        topic = f"/openhab/command/{self._item_name}"

        self._publisher = self.create_publisher(msg_class, topic, 10)
        self.get_logger().info(
            f"Publishing to {topic}  [{msg_class.__name__}]\n"
            f"  item_name : {self._item_name}\n"
            f"  command   : {self._command}\n"
            f"  once      : {self._publish_once}"
        )

        if self._publish_once:
            # Publish once after a short delay (allow subscriber to connect)
            self._timer = self.create_timer(0.2, self._publish_once_cb)
        else:
            period = 1.0 / max(self._rate_hz, 0.001)
            self._timer = self.create_timer(period, self._publish_cb)

    def _publish_once_cb(self):
        self._publish_cb()
        self._timer.cancel()
        self.get_logger().info("Published once – shutting down.")
        raise SystemExit

    def _publish_cb(self):
        msg = _build_command_msg(
            self, self._item_type, self._item_name, self._command
        )
        self._publisher.publish(msg)
        self.get_logger().info(
            f"Published: {self._item_name} ← {self._command}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABCommandPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
