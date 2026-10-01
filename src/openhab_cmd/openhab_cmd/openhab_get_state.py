#!/usr/bin/env python3
"""
openhab_get_state.py
====================
Generic service client: query the state of ANY openHAB item by name.
The item type is passed as a parameter to determine which service to call.

Parameters (--ros-args -p):
    item_name  (string, required) – openHAB item name
    item_type  (string, default: "Switch") – one of:
               Call, Color, Contact, DateTime, Dimmer, Image, Location,
               Number, Player, Rollershutter, String, Switch

Usage:
    ros2 run openhab_cmd openhab_get_state.py \
        --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch

    ros2 run openhab_cmd openhab_get_state.py \
        --ros-args -p item_name:=RoomTemperature -p item_type:=Number
"""

import rclpy
from rclpy.node import Node

from openhab_msgs.srv import (
    GetCallState, GetColorState, GetContactState, GetDateTimeState,
    GetDimmerState, GetImageState, GetLocationState, GetNumberState,
    GetPlayerState, GetRollershutterState, GetStringState, GetSwitchState,
)

# Map item type → (srv_class, service_topic)
SERVICE_MAP = {
    "Call":          (GetCallState,          "/openhab/get_state/call"),
    "Color":         (GetColorState,         "/openhab/get_state/color"),
    "Contact":       (GetContactState,       "/openhab/get_state/contact"),
    "DateTime":      (GetDateTimeState,      "/openhab/get_state/datetime"),
    "Dimmer":        (GetDimmerState,        "/openhab/get_state/dimmer"),
    "Image":         (GetImageState,         "/openhab/get_state/image"),
    "Location":      (GetLocationState,      "/openhab/get_state/location"),
    "Number":        (GetNumberState,        "/openhab/get_state/number"),
    "Player":        (GetPlayerState,        "/openhab/get_state/player"),
    "Rollershutter": (GetRollershutterState, "/openhab/get_state/rollershutter"),
    "String":        (GetStringState,        "/openhab/get_state/string"),
    "Switch":        (GetSwitchState,        "/openhab/get_state/switch"),
}


class OpenHABGetStateClient(Node):
    def __init__(self):
        super().__init__("openhab_get_state")

        self.declare_parameter("item_name", "")
        self.declare_parameter("item_type", "Switch")

        self.item_name = self.get_parameter("item_name").get_parameter_value().string_value
        self.item_type = self.get_parameter("item_type").get_parameter_value().string_value

        if not self.item_name:
            self.get_logger().error("Parameter 'item_name' is required!")
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

    def send_request(self):
        if not self.item_name or self.item_type not in SERVICE_MAP:
            return

        srv_class, srv_topic = SERVICE_MAP[self.item_type]
        request = srv_class.Request()
        request.item_name = self.item_name

        self.get_logger().info(
            f"Requesting state of '{self.item_name}' ({self.item_type}) ..."
        )

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()

        if response is None:
            self.get_logger().error("No response received!")
            return

        if response.success:
            self._print_response(response)
        else:
            self.get_logger().error(f"Service call failed: {response.message}")

    def _print_response(self, response):
        """Print all relevant fields of the state response."""
        state = response.state
        self.get_logger().info(
            f"[{self.item_type}] {self.item_name} state:"
        )
        # Always print raw state
        if hasattr(state, "state"):
            self.get_logger().info(f"  state   : {state.state}")
        # Type-specific extra fields
        if self.item_type == "Color":
            self.get_logger().info(f"  hue     : {state.hue}")
            self.get_logger().info(f"  sat     : {state.saturation}")
            self.get_logger().info(f"  bri     : {state.brightness}")
        elif self.item_type == "Location":
            self.get_logger().info(f"  lat     : {state.latitude}")
            self.get_logger().info(f"  lon     : {state.longitude}")
            self.get_logger().info(f"  alt     : {state.altitude}")
        elif self.item_type == "Number":
            self.get_logger().info(f"  unit    : {state.unit}")


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABGetStateClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
