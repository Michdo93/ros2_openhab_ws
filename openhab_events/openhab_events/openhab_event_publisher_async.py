#!/usr/bin/env python3
"""
openhab_event_publisher_async.py
=================================
Async variant of the SSE publisher using AsyncItemEvents.
Uses asyncio + rclpy executor integration.

Same parameters and topic schema as openhab_event_publisher.py.
Use this version when you need to run other async tasks alongside
the SSE stream in the same process.

Usage:
    ros2 run openhab_events openhab_event_publisher_async.py \
        --ros-args \
        -p openhab_url:=http://192.168.1.100:8080 \
        -p openhab_token:=oh.openhab.YourTokenHere \
        -p item_type_map:='{"LivingRoomLight":"Switch","Temp1":"Number"}'
"""

import json
import asyncio
import threading

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import Header

from openhab_msgs.msg import (
    CallState, ColorState, ContactState, DateTimeState, DimmerState,
    ImageState, LocationState, NumberState, PlayerState,
    RollershutterState, StringState, SwitchState,
)

try:
    from openhab import OpenHABClient
    from openhab import AsyncItemEvents
    OPENHAB_AVAILABLE = True
except ImportError:
    try:
        from openhab import OpenHABClient, ItemEvents as AsyncItemEvents
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


def _build_msg(node, item_name, item_type, state_value):
    """Build typed state message - same logic as sync publisher."""
    h = _make_header(node)

    builders = {
        "Switch": lambda: _sw(h, item_name, state_value),
        "Dimmer": lambda: _dim(h, item_name, state_value),
        "Color": lambda: _col(h, item_name, state_value),
        "Contact": lambda: _contact(h, item_name, state_value),
        "DateTime": lambda: _dt(h, item_name, state_value),
        "Image": lambda: _img(h, item_name, state_value),
        "Location": lambda: _loc(h, item_name, state_value),
        "Number": lambda: _num(h, item_name, state_value),
        "Player": lambda: _player(h, item_name, state_value),
        "Rollershutter": lambda: _roller(h, item_name, state_value),
        "Call": lambda: _call(h, item_name, state_value),
    }

    builder = builders.get(item_type)
    if builder:
        return builder()

    msg = StringState()
    msg.header = h; msg.item_name = item_name; msg.state = state_value
    return msg


def _sw(h, n, v):
    m = SwitchState(); m.header = h; m.item_name = n; m.state = v; return m

def _dim(h, n, v):
    m = DimmerState(); m.header = h; m.item_name = n
    try: m.state = float(v)
    except: m.state = 0.0
    return m

def _col(h, n, v):
    hue, s, b = _parse_color(v)
    m = ColorState(); m.header = h; m.item_name = n
    m.hue = hue; m.saturation = s; m.brightness = b; m.state = v; return m

def _contact(h, n, v):
    m = ContactState(); m.header = h; m.item_name = n; m.state = v; return m

def _dt(h, n, v):
    m = DateTimeState(); m.header = h; m.item_name = n; m.state = v; return m

def _img(h, n, v):
    m = ImageState(); m.header = h; m.item_name = n; m.state = v
    m.data = []; m.content_type = ""; return m

def _loc(h, n, v):
    lat, lon, alt = _parse_location(v)
    m = LocationState(); m.header = h; m.item_name = n
    m.latitude = lat; m.longitude = lon; m.altitude = alt; m.state = v; return m

def _num(h, n, v):
    parts = v.split(" ", 1)
    m = NumberState(); m.header = h; m.item_name = n
    try: m.state = float(parts[0])
    except: m.state = 0.0
    m.unit = parts[1] if len(parts) > 1 else ""; return m

def _player(h, n, v):
    m = PlayerState(); m.header = h; m.item_name = n; m.state = v; return m

def _roller(h, n, v):
    m = RollershutterState(); m.header = h; m.item_name = n
    try: m.state = float(v)
    except: m.state = 0.0
    return m

def _call(h, n, v):
    m = CallState(); m.header = h; m.item_name = n; m.state = v; return m


MSG_TYPE_MAP = {
    "Switch": SwitchState,
    "Dimmer": DimmerState,
    "Color": ColorState,
    "Contact": ContactState,
    "DateTime": DateTimeState,
    "Image": ImageState,
    "Location": LocationState,
    "Number": NumberState,
    "Player": PlayerState,
    "Rollershutter": RollershutterState,
    "Call": CallState,
    "String": StringState,
}


class OpenHABEventPublisherAsync(Node):
    """Async SSE publisher using AsyncItemEvents."""

    def __init__(self):
        super().__init__("openhab_event_publisher_async")

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
        self._qsize = self.get_parameter("queue_size").get_parameter_value().integer_value

        self._item_type_map: dict = {}
        if type_map_json:
            try:
                self._item_type_map = json.loads(type_map_json)
                self.get_logger().info(
                    f"Item type map: {len(self._item_type_map)} entries"
                )
            except json.JSONDecodeError as e:
                self.get_logger().error(f"item_type_map parse error: {e}")

        self._publishers: dict = {}

        if not OPENHAB_AVAILABLE:
            self.get_logger().error(
                "python-openhab-rest-client not installed!"
            )
            return

        if token:
            client = OpenHABClient(url=url, token=token)
        else:
            client = OpenHABClient(url=url, username=user, password=password)

        self._async_item_events = AsyncItemEvents(client)
        self.get_logger().info(
            f"[Async] Listening for ItemStateChangedEvents from {url}"
        )

        # Run asyncio loop in background thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True
        )
        self._thread.start()

    def _run_loop(self):
        self._loop.run_until_complete(self._sse_loop())

    async def _sse_loop(self):
        try:
            # AsyncItemEvents.ItemStateChangedEvent() returns an async generator
            async for data in self._async_item_events.ItemStateChangedEvent():
                if not rclpy.ok():
                    break
                if not isinstance(data, dict):
                    continue
                if data.get("type") != "ItemStateChangedEvent":
                    continue

                topic_str = data.get("topic", "")
                parts = topic_str.split("/")
                if len(parts) < 3:
                    continue
                item_name = parts[2]

                try:
                    payload = json.loads(data.get("payload", "{}"))
                except json.JSONDecodeError:
                    continue

                state_value = payload.get("value", "")
                item_type = self._item_type_map.get(item_name, "String")

                try:
                    msg = _build_msg(self, item_name, item_type, state_value)
                    pub = self._get_or_create_publisher(item_name, item_type)
                    pub.publish(msg)
                    self.get_logger().debug(
                        f"[Async] Published {item_name} = {state_value}"
                    )
                except Exception as e:
                    self.get_logger().warn(
                        f"[Async] Could not publish {item_name}: {e}"
                    )
        except Exception as e:
            self.get_logger().error(f"[Async] SSE loop error: {e}")

    def _get_or_create_publisher(self, item_name: str, item_type: str):
        if item_name not in self._publishers:
            msg_class = MSG_TYPE_MAP.get(item_type, StringState)
            topic = f"/openhab/state/{item_name}"
            pub = self.create_publisher(msg_class, topic, self._qsize)
            self._publishers[item_name] = pub
            self.get_logger().info(
                f"[Async] Created publisher: {topic}  [{msg_class.__name__}]"
            )
        return self._publishers[item_name]


def main(args=None):
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()
    node = OpenHABEventPublisherAsync()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
