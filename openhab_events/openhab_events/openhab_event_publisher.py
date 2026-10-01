#!/usr/bin/env python3
"""
openhab_event_publisher.py
==========================
ROS2 node that listens to openHAB ItemStateChangedEvents via SSE and
publishes the resulting state on a per-item ROS2 topic.

Topic schema:
    /openhab/state/<ItemName>  →  typed openhab_msgs/msg/*State message

The node auto-detects the item type from the event payload and publishes
the correct message type.  A catch-all StringState is used as fallback.

Parameters:
    openhab_url         (string,  default: "http://127.0.0.1:8080")
    openhab_token       (string,  default: "")
    openhab_user        (string,  default: "openhab")
    openhab_password    (string,  default: "habopen")
    item_type_map       (string,  default: "")
        JSON dict mapping item names to types, e.g.:
        '{"mySwitch":"Switch","myDimmer":"Dimmer","myColor":"Color"}'
        Required to publish the correct typed message.
        Items NOT in the map are published as StringState (fallback).
    queue_size          (int,     default: 10)

Usage:
    ros2 run openhab_events openhab_event_publisher.py \
        --ros-args \
        -p openhab_url:=http://192.168.1.100:8080 \
        -p openhab_token:=oh.openhab.xxxx \
        -p item_type_map:='{"LivingRoomLight":"Switch","Dimmer1":"Dimmer"}'
"""

import json
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header

from openhab_msgs.msg import (
    CallState, ColorState, ContactState, DateTimeState, DimmerState,
    ImageState, LocationState, NumberState, PlayerState,
    RollershutterState, StringState, SwitchState,
)

try:
    from openhab import OpenHABClient, ItemEvents
    OPENHAB_AVAILABLE = True
except ImportError:
    OPENHAB_AVAILABLE = False


def _make_header(node: Node) -> Header:
    h = Header()
    h.stamp = node.get_clock().now().to_msg()
    h.frame_id = ""
    return h


def _parse_color(raw: str):
    try:
        p = raw.split(",")
        return float(p[0]), float(p[1]), float(p[2])
    except Exception:
        return 0.0, 0.0, 0.0


def _parse_location(raw: str):
    try:
        p = raw.split(",")
        lat = float(p[0])
        lon = float(p[1])
        alt = float(p[2]) if len(p) > 2 else 0.0
        return lat, lon, alt
    except Exception:
        return 0.0, 0.0, 0.0


# Map item type string → msg_class
_TYPE_MAP = {
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


def _build_msg(node: Node, item_name: str, item_type: str, state_value: str):
    """Build a typed state message from raw SSE data."""
    h = _make_header(node)

    if item_type == "Switch":
        msg = SwitchState()
        msg.header = h; msg.item_name = item_name; msg.state = state_value
        return msg

    if item_type == "Dimmer":
        msg = DimmerState()
        msg.header = h; msg.item_name = item_name
        try: msg.state = float(state_value)
        except Exception: msg.state = 0.0
        return msg

    if item_type == "Color":
        h2, s, b = _parse_color(state_value)
        msg = ColorState()
        msg.header = h; msg.item_name = item_name
        msg.hue = h2; msg.saturation = s; msg.brightness = b
        msg.state = state_value
        return msg

    if item_type == "Contact":
        msg = ContactState()
        msg.header = h; msg.item_name = item_name; msg.state = state_value
        return msg

    if item_type == "DateTime":
        msg = DateTimeState()
        msg.header = h; msg.item_name = item_name; msg.state = state_value
        return msg

    if item_type == "Image":
        msg = ImageState()
        msg.header = h; msg.item_name = item_name; msg.state = state_value
        msg.data = []; msg.content_type = ""
        return msg

    if item_type == "Location":
        lat, lon, alt = _parse_location(state_value)
        msg = LocationState()
        msg.header = h; msg.item_name = item_name
        msg.latitude = lat; msg.longitude = lon; msg.altitude = alt
        msg.state = state_value
        return msg

    if item_type in ("Number", "Number:dimension"):
        parts = state_value.split(" ", 1)
        msg = NumberState()
        msg.header = h; msg.item_name = item_name
        try: msg.state = float(parts[0])
        except Exception: msg.state = 0.0
        msg.unit = parts[1] if len(parts) > 1 else ""
        return msg

    if item_type == "Player":
        msg = PlayerState()
        msg.header = h; msg.item_name = item_name; msg.state = state_value
        return msg

    if item_type == "Rollershutter":
        msg = RollershutterState()
        msg.header = h; msg.item_name = item_name
        try: msg.state = float(state_value)
        except Exception: msg.state = 0.0
        return msg

    if item_type == "Call":
        msg = CallState()
        msg.header = h; msg.item_name = item_name; msg.state = state_value
        return msg

    # Fallback: StringState
    msg = StringState()
    msg.header = h; msg.item_name = item_name; msg.state = state_value
    return msg


def _msg_type_for(item_type: str):
    """Return the ROS2 message class for a given openHAB item type string."""
    return _TYPE_MAP.get(item_type, StringState)


class OpenHABEventPublisher(Node):
    """
    Listens to openHAB SSE ItemStateChangedEvents in a background thread
    and publishes typed state messages on /openhab/state/<ItemName>.
    """

    def __init__(self):
        super().__init__("openhab_event_publisher")

        self.declare_parameter("openhab_url",      "http://127.0.0.1:8080")
        self.declare_parameter("openhab_token",    "")
        self.declare_parameter("openhab_user",     "openhab")
        self.declare_parameter("openhab_password", "habopen")
        self.declare_parameter("item_type_map",    "")
        self.declare_parameter("queue_size",       10)

        url      = self.get_parameter("openhab_url").get_parameter_value().string_value
        token    = self.get_parameter("openhab_token").get_parameter_value().string_value
        user     = self.get_parameter("openhab_user").get_parameter_value().string_value
        password = self.get_parameter("openhab_password").get_parameter_value().string_value
        type_map_json = self.get_parameter("item_type_map").get_parameter_value().string_value
        self._qsize  = self.get_parameter("queue_size").get_parameter_value().integer_value

        # Parse item→type map
        self._item_type_map: dict = {}
        if type_map_json:
            try:
                self._item_type_map = json.loads(type_map_json)
                self.get_logger().info(
                    f"Item type map loaded: {len(self._item_type_map)} entries"
                )
            except json.JSONDecodeError as e:
                self.get_logger().error(f"Could not parse item_type_map: {e}")

        # publishers cache: item_name → publisher
        self._publishers: dict = {}

        if not OPENHAB_AVAILABLE:
            self.get_logger().error(
                "python-openhab-rest-client not installed! "
                "Run: pip install python-openhab-rest-client"
            )
            return

        # Setup SSE client
        if token:
            client = OpenHABClient(url=url, token=token)
        else:
            client = OpenHABClient(url=url, username=user, password=password)

        self._item_events = ItemEvents(client)
        self.get_logger().info(f"Listening for ItemStateChangedEvents from {url}")

        # Start SSE listener in background thread
        self._sse_thread = threading.Thread(
            target=self._sse_loop, daemon=True
        )
        self._sse_thread.start()

    def _get_or_create_publisher(self, item_name: str, item_type: str):
        """Return existing publisher or create a new one for item_name."""
        if item_name not in self._publishers:
            msg_class = _msg_type_for(item_type)
            topic = f"/openhab/state/{item_name}"
            pub = self.create_publisher(msg_class, topic, self._qsize)
            self._publishers[item_name] = pub
            self.get_logger().info(
                f"Created publisher: {topic}  [{msg_class.__name__}]"
            )
        return self._publishers[item_name]

    def _sse_loop(self):
        """Background thread: process SSE stream from openHAB."""
        try:
            # Subscribe to ALL item state changes (wildcard "*")
            response = self._item_events.ItemStateChangedEvent()

            with response as events:
                for line in events.iter_lines():
                    if not rclpy.ok():
                        break

                    line = line.decode("utf-8", errors="replace")
                    if "data" not in line:
                        continue

                    line = line.replace("data: ", "")
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # openHAB SSE payload structure:
                    # {
                    #   "topic": "openhab/items/<ItemName>/statechanged",
                    #   "payload": "{\"type\":\"OnOff\",\"value\":\"ON\",...}",
                    #   "type": "ItemStateChangedEvent"
                    # }
                    if data.get("type") != "ItemStateChangedEvent":
                        continue

                    topic_str = data.get("topic", "")
                    # Extract item name from topic path
                    # e.g. "openhab/items/LivingRoomLight/statechanged"
                    parts = topic_str.split("/")
                    if len(parts) < 3:
                        continue
                    item_name = parts[2]

                    # Parse payload
                    try:
                        payload = json.loads(data.get("payload", "{}"))
                    except json.JSONDecodeError:
                        continue

                    state_value = payload.get("value", "")

                    # Determine item type
                    item_type = self._item_type_map.get(item_name, "String")

                    # Build and publish message
                    try:
                        msg = _build_msg(self, item_name, item_type, state_value)
                        pub = self._get_or_create_publisher(item_name, item_type)
                        pub.publish(msg)
                        self.get_logger().debug(
                            f"Published {item_name} = {state_value}"
                        )
                    except Exception as e:
                        self.get_logger().warn(
                            f"Could not publish {item_name}: {e}"
                        )

        except Exception as e:
            self.get_logger().error(f"SSE loop error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABEventPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
