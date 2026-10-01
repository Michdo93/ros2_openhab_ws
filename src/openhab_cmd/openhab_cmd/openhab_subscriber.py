#!/usr/bin/env python3
"""
openhab_subscriber.py
=====================
Generic subscriber: subscribe to ANY openHAB item topic and print
its state changes to the terminal.

This is the "debugging/testing" node – no fixed item name needed.
The item name and type are passed as ROS2 node parameters at runtime.

Parameters (--ros-args -p):
    item_name  (string, required) – openHAB item name to subscribe to
    item_type  (string, default: "Switch") – one of:
               Call, Color, Contact, DateTime, Dimmer, Image, Location,
               Number, Player, Rollershutter, String, Switch

The node subscribes to /openhab/state/<item_name> and prints every
received message to the console.

Usage:
    ros2 run openhab_cmd openhab_subscriber.py \
        --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch

    ros2 run openhab_cmd openhab_subscriber.py \
        --ros-args -p item_name:=RoomTemperature -p item_type:=Number

    ros2 run openhab_cmd openhab_subscriber.py \
        --ros-args -p item_name:=LivingRoomColor -p item_type:=Color
"""

import rclpy
from rclpy.node import Node

from openhab_msgs.msg import (
    CallState, ColorState, ContactState, DateTimeState, DimmerState,
    ImageState, LocationState, NumberState, PlayerState,
    RollershutterState, StringState, SwitchState,
)

MSG_MAP = {
    "Call":          CallState,
    "Color":         ColorState,
    "Contact":       ContactState,
    "DateTime":      DateTimeState,
    "Dimmer":        DimmerState,
    "Image":         ImageState,
    "Location":      LocationState,
    "Number":        NumberState,
    "Player":        PlayerState,
    "Rollershutter": RollershutterState,
    "String":        StringState,
    "Switch":        SwitchState,
}


def _format_msg(item_type: str, msg) -> str:
    """Return a human-readable string for any state message."""
    lines = [f"[{item_type}] item: {msg.item_name}"]
    if item_type == "Color":
        lines.append(f"  state      : {msg.state}")
        lines.append(f"  hue        : {msg.hue}")
        lines.append(f"  saturation : {msg.saturation}")
        lines.append(f"  brightness : {msg.brightness}")
    elif item_type == "Location":
        lines.append(f"  state      : {msg.state}")
        lines.append(f"  latitude   : {msg.latitude}")
        lines.append(f"  longitude  : {msg.longitude}")
        lines.append(f"  altitude   : {msg.altitude}")
    elif item_type == "Number":
        lines.append(f"  state      : {msg.state}")
        lines.append(f"  unit       : {msg.unit}")
    elif item_type == "Dimmer":
        lines.append(f"  state      : {msg.state} %")
    elif item_type == "Rollershutter":
        lines.append(f"  state      : {msg.state} %")
    else:
        lines.append(f"  state      : {msg.state}")
    return "\n".join(lines)


class OpenHABSubscriber(Node):
    def __init__(self):
        super().__init__("openhab_subscriber")

        self.declare_parameter("item_name", "")
        self.declare_parameter("item_type", "Switch")

        item_name = self.get_parameter("item_name").get_parameter_value().string_value
        item_type = self.get_parameter("item_type").get_parameter_value().string_value

        if not item_name:
            self.get_logger().error(
                "Parameter 'item_name' is required! "
                "Use: --ros-args -p item_name:=<YourItemName>"
            )
            return

        if item_type not in MSG_MAP:
            self.get_logger().warn(
                f"Unknown item_type '{item_type}', falling back to 'String'. "
                f"Valid: {list(MSG_MAP.keys())}"
            )
            item_type = "String"

        self._item_type = item_type
        topic = f"/openhab/state/{item_name}"
        msg_class = MSG_MAP[item_type]

        self.subscription = self.create_subscription(
            msg_class,
            topic,
            self._callback,
            10,
        )
        self.get_logger().info(
            f"Subscribed to {topic}  [{msg_class.__name__}]\n"
            f"Waiting for state changes ..."
        )

    def _callback(self, msg):
        self.get_logger().info(
            "\n" + _format_msg(self._item_type, msg)
        )


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
