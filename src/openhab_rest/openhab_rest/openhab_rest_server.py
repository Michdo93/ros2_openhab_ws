#!/usr/bin/env python3
"""
openhab_rest_server.py
======================
ROS2 service server that bridges openHAB REST API calls.

Advertises:
  GetState services:
    /openhab/get_state/call         (openhab_msgs/srv/GetCallState)
    /openhab/get_state/color        (openhab_msgs/srv/GetColorState)
    /openhab/get_state/contact      (openhab_msgs/srv/GetContactState)
    /openhab/get_state/datetime     (openhab_msgs/srv/GetDateTimeState)
    /openhab/get_state/dimmer       (openhab_msgs/srv/GetDimmerState)
    /openhab/get_state/image        (openhab_msgs/srv/GetImageState)
    /openhab/get_state/location     (openhab_msgs/srv/GetLocationState)
    /openhab/get_state/number       (openhab_msgs/srv/GetNumberState)
    /openhab/get_state/player       (openhab_msgs/srv/GetPlayerState)
    /openhab/get_state/rollershutter(openhab_msgs/srv/GetRollershutterState)
    /openhab/get_state/string       (openhab_msgs/srv/GetStringState)
    /openhab/get_state/switch       (openhab_msgs/srv/GetSwitchState)

  SendCommand services:
    /openhab/send_command/color        (openhab_msgs/srv/SendColorCommand)
    /openhab/send_command/contact      (openhab_msgs/srv/SendContactCommand)
    /openhab/send_command/datetime     (openhab_msgs/srv/SendDateTimeCommand)
    /openhab/send_command/dimmer       (openhab_msgs/srv/SendDimmerCommand)
    /openhab/send_command/location     (openhab_msgs/srv/SendLocationCommand)
    /openhab/send_command/number       (openhab_msgs/srv/SendNumberCommand)
    /openhab/send_command/player       (openhab_msgs/srv/SendPlayerCommand)
    /openhab/send_command/rollershutter(openhab_msgs/srv/SendRollershutterCommand)
    /openhab/send_command/string       (openhab_msgs/srv/SendStringCommand)
    /openhab/send_command/switch       (openhab_msgs/srv/SendSwitchCommand)

Parameters (ROS2 node parameters):
    openhab_url      (string, default: "http://127.0.0.1:8080")
    openhab_token    (string, default: "")
    openhab_user     (string, default: "openhab")
    openhab_password (string, default: "habopen")

Usage:
    ros2 run openhab_rest openhab_rest_server.py \
        --ros-args -p openhab_url:=http://192.168.1.100:8080 \
                   -p openhab_token:=oh.openhab.xxxx
"""

import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Time
import datetime

from openhab_msgs.msg import (
    CallState, ColorState, ContactState, DateTimeState, DimmerState,
    ImageState, LocationState, NumberState, PlayerState,
    RollershutterState, StringState, SwitchState,
)
from openhab_msgs.srv import (
    GetCallState, GetColorState, GetContactState, GetDateTimeState,
    GetDimmerState, GetImageState, GetLocationState, GetNumberState,
    GetPlayerState, GetRollershutterState, GetStringState, GetSwitchState,
    SendColorCommand, SendContactCommand, SendDateTimeCommand,
    SendDimmerCommand, SendLocationCommand, SendNumberCommand,
    SendPlayerCommand, SendRollershutterCommand, SendStringCommand,
    SendSwitchCommand,
)

try:
    from openhab import OpenHABClient, Items
    OPENHAB_AVAILABLE = True
except ImportError:
    OPENHAB_AVAILABLE = False


def _now_header(node: Node):
    """Return a populated std_msgs/Header with current ROS time."""
    from std_msgs.msg import Header
    h = Header()
    t = node.get_clock().now().to_msg()
    h.stamp = t
    h.frame_id = ""
    return h


def _parse_color(raw: str):
    """Parse 'H,S,B' string → (hue, sat, bri) floats, robust."""
    try:
        parts = raw.split(",")
        return float(parts[0]), float(parts[1]), float(parts[2])
    except Exception:
        return 0.0, 0.0, 0.0


def _parse_location(raw: str):
    """Parse 'lat,lon[,alt]' → (lat, lon, alt) floats."""
    try:
        parts = raw.split(",")
        lat = float(parts[0])
        lon = float(parts[1])
        alt = float(parts[2]) if len(parts) > 2 else 0.0
        return lat, lon, alt
    except Exception:
        return 0.0, 0.0, 0.0


class OpenHABRestServer(Node):
    """
    Single ROS2 node that exposes all GetState and SendCommand services
    and handles the REST communication with openHAB.
    """

    def __init__(self):
        super().__init__("openhab_rest_server")

        # ── Declare & read parameters ─────────────────────────────────────
        self.declare_parameter("openhab_url", "http://127.0.0.1:8080")
        self.declare_parameter("openhab_token", "")
        self.declare_parameter("openhab_user", "openhab")
        self.declare_parameter("openhab_password", "habopen")

        url = self.get_parameter("openhab_url").get_parameter_value().string_value
        token = self.get_parameter("openhab_token").get_parameter_value().string_value
        user = self.get_parameter("openhab_user").get_parameter_value().string_value
        password = self.get_parameter("openhab_password").get_parameter_value().string_value

        self.get_logger().info(f"Connecting to openHAB at {url}")

        # ── Setup openHAB REST client ────────────────────────────────────
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
            self.get_logger().info("openHAB REST client initialized.")

        # ── GetState services ─────────────────────────────────────────────
        self.create_service(GetCallState,          "/openhab/get_state/call",          self._get_call_state)
        self.create_service(GetColorState,         "/openhab/get_state/color",         self._get_color_state)
        self.create_service(GetContactState,       "/openhab/get_state/contact",       self._get_contact_state)
        self.create_service(GetDateTimeState,      "/openhab/get_state/datetime",      self._get_datetime_state)
        self.create_service(GetDimmerState,        "/openhab/get_state/dimmer",        self._get_dimmer_state)
        self.create_service(GetImageState,         "/openhab/get_state/image",         self._get_image_state)
        self.create_service(GetLocationState,      "/openhab/get_state/location",      self._get_location_state)
        self.create_service(GetNumberState,        "/openhab/get_state/number",        self._get_number_state)
        self.create_service(GetPlayerState,        "/openhab/get_state/player",        self._get_player_state)
        self.create_service(GetRollershutterState, "/openhab/get_state/rollershutter", self._get_rollershutter_state)
        self.create_service(GetStringState,        "/openhab/get_state/string",        self._get_string_state)
        self.create_service(GetSwitchState,        "/openhab/get_state/switch",        self._get_switch_state)

        # ── SendCommand services ──────────────────────────────────────────
        self.create_service(SendColorCommand,         "/openhab/send_command/color",         self._send_color_cmd)
        self.create_service(SendContactCommand,       "/openhab/send_command/contact",       self._send_contact_cmd)
        self.create_service(SendDateTimeCommand,      "/openhab/send_command/datetime",      self._send_datetime_cmd)
        self.create_service(SendDimmerCommand,        "/openhab/send_command/dimmer",        self._send_dimmer_cmd)
        self.create_service(SendLocationCommand,      "/openhab/send_command/location",      self._send_location_cmd)
        self.create_service(SendNumberCommand,        "/openhab/send_command/number",        self._send_number_cmd)
        self.create_service(SendPlayerCommand,        "/openhab/send_command/player",        self._send_player_cmd)
        self.create_service(SendRollershutterCommand, "/openhab/send_command/rollershutter", self._send_rollershutter_cmd)
        self.create_service(SendStringCommand,        "/openhab/send_command/string",        self._send_string_cmd)
        self.create_service(SendSwitchCommand,        "/openhab/send_command/switch",        self._send_switch_cmd)

        self.get_logger().info("All GetState and SendCommand services ready.")

    # ── Internal helpers ─────────────────────────────────────────────────

    def _fetch_raw_state(self, item_name: str):
        """Returns raw state string from openHAB or raises on error."""
        if self._items is None:
            raise RuntimeError("openHAB client not available. Check python-openhab-rest-client installation.")
        data = self._items.getItemState(item_name)
        # getItemState returns the raw state string directly
        if isinstance(data, dict):
            return str(data.get("state", ""))
        return str(data)

    def _send_command(self, item_name: str, command: str):
        """Sends a command to openHAB, returns (success, message)."""
        if self._items is None:
            return False, "openHAB client not available. Check python-openhab-rest-client installation."
        try:
            self._items.sendCommand(item_name, command)
            return True, f"Command '{command}' sent to '{item_name}'"
        except Exception as e:
            return False, str(e)

    # ── GetState callbacks ────────────────────────────────────────────────

    def _get_call_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = CallState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_color_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            h, s, b = _parse_color(raw)
            msg = ColorState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.hue = h
            msg.saturation = s
            msg.brightness = b
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_contact_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = ContactState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_datetime_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = DateTimeState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_dimmer_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = DimmerState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = float(raw) if raw not in ("NULL", "UNDEF", "") else 0.0
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_image_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = ImageState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            msg.data = []
            msg.content_type = ""
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_location_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            lat, lon, alt = _parse_location(raw)
            msg = LocationState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.latitude = lat
            msg.longitude = lon
            msg.altitude = alt
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_number_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            # State may be "23.5 °C" or just "23.5"
            parts = raw.split(" ", 1)
            val = float(parts[0]) if parts[0] not in ("NULL", "UNDEF", "") else 0.0
            unit = parts[1] if len(parts) > 1 else ""
            msg = NumberState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = val
            msg.unit = unit
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_player_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = PlayerState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_rollershutter_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = RollershutterState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = float(raw) if raw not in ("NULL", "UNDEF", "") else 0.0
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_string_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = StringState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    def _get_switch_state(self, request, response):
        try:
            raw = self._fetch_raw_state(request.item_name)
            msg = SwitchState()
            msg.header = _now_header(self)
            msg.item_name = request.item_name
            msg.state = raw
            response.state = msg
            response.success = True
            response.message = ""
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

    # ── SendCommand callbacks ─────────────────────────────────────────────

    def _send_color_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_contact_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_datetime_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_dimmer_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_location_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_number_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_player_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_rollershutter_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_string_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response

    def _send_switch_cmd(self, request, response):
        ok, msg = self._send_command(request.item_name, request.command)
        response.success = ok
        response.message = msg
        return response


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABRestServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
