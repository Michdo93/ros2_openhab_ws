"""openhab_bridge – connects openHAB items with the ROS 2 graph.

openHAB -> ROS 2
    /openhab/items/<Item>/state    openhab_msgs/ItemState   (transient local: late joiners
                                                             get the last state)
    /openhab/items/<Item>/value    std_msgs/Float64         (numeric items, publish_value)
ROS 2 -> openHAB
    /openhab/items/<Item>/command  std_msgs/String          command for one item
    /openhab/command               openhab_msgs/ItemCommand command or update for any item
    ros_inputs                     any topic with a 'data' field -> state update or command
Services
    /openhab/get_item, /openhab/send_command, /openhab/list_items
Diagnostics
    /diagnostics                   diagnostic_msgs/DiagnosticArray (connection, counters)

Address and token come from the environment (OPENHAB_URL, OPENHAB_TOKEN) – never from
parameters, because every participant can read parameters with 'ros2 param get'.
"""
import importlib
import os
import threading
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from openhab import ItemEvents, Items, OpenHABClient, iterSSEEvents
from openhab_msgs.msg import ItemCommand, ItemState
from openhab_msgs.srv import GetItem, ListItems, SendCommand
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Float64, String

from .state import parse_mapping, parse_state, to_openhab

STATE_QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL)


def _error(result):
    """python-openhab-rest-client returns {'error': ...} instead of raising."""
    return result.get("error") if isinstance(result, dict) else None


class OpenHABBridge(Node):
    def __init__(self):
        super().__init__("openhab_bridge")
        self.declare_parameter("items", [""])
        self.declare_parameter("groups", [""])
        self.declare_parameter("tags", [""])
        self.declare_parameter("namespace", "openhab")
        self.declare_parameter("publish_value", True)
        self.declare_parameter("ros_inputs", [""])
        self.declare_parameter("command_source", "ros2")
        self.declare_parameter("reconnect_delay", 5.0)

        p = lambda n: self.get_parameter(n).value  # noqa: E731
        self.ns = "/" + p("namespace").strip("/")
        self.source = p("command_source")
        self.reconnect_delay = float(p("reconnect_delay"))
        self.publish_value = bool(p("publish_value"))

        url = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
        token = os.environ.get("OPENHAB_TOKEN") or None
        self.client = OpenHABClient(url, token=token)
        self.items_api = Items(self.client)
        self.url = url

        self.types = {}          # item name -> (type, groupType)
        self.state_pub = {}      # item name -> publisher ItemState
        self.value_pub = {}      # item name -> publisher Float64
        self.cmd_sub = []
        self.counters = {"events": 0, "commands": 0, "updates": 0, "errors": 0}
        self.connected = False
        self._stop = threading.Event()

        names = self._resolve(clean(p("items")), clean(p("groups")), clean(p("tags")))
        for name in names:
            self._add_item(name)

        self.create_subscription(ItemCommand, f"{self.ns}/command", self._on_item_command, 10)
        self.create_service(GetItem, f"{self.ns}/get_item", self._srv_get_item)
        self.create_service(SendCommand, f"{self.ns}/send_command", self._srv_send_command)
        self.create_service(ListItems, f"{self.ns}/list_items", self._srv_list_items)
        for entry in clean(p("ros_inputs")):
            self._add_ros_input(entry)

        self.diag_pub = self.create_publisher(DiagnosticArray, "/diagnostics", 10)
        self.create_timer(5.0, self._publish_diagnostics)

        self._reader = threading.Thread(target=self._read_events, daemon=True)
        self._reader.start()
        self.get_logger().info(f"bridge to {url}: {len(self.types)} items under {self.ns}/items")

    # ------------------------------------------------------------------ setup
    def _resolve(self, items, groups, tags):
        """Explicit items + members of groups + items with tags; empty = all items."""
        wanted = list(items)
        for group in groups:
            data = self.items_api.getItem(group)
            if _error(data):
                self.get_logger().error(f"group {group}: {_error(data)}")
                continue
            wanted.append(group)
            wanted += [m["name"] for m in data.get("members", [])]
        for tag in tags:
            data = self.items_api.getItems(tags=tag, fields="name")
            if not _error(data):
                wanted += [i["name"] for i in data]
        if not (items or groups or tags):
            data = self.items_api.getItems(fields="name")
            wanted = [] if _error(data) else [i["name"] for i in data]
        return list(dict.fromkeys(wanted))  # unique, keeps order

    def _add_item(self, name):
        data = self.items_api.getItem(name, metadata="")
        if _error(data):
            self.get_logger().error(f"item {name}: {_error(data)}")
            return False
        self.types[name] = (data.get("type", "String"), data.get("groupType", ""))
        base = f"{self.ns}/items/{name}"
        self.state_pub[name] = self.create_publisher(ItemState, f"{base}/state", STATE_QOS)
        if self.publish_value:
            self.value_pub[name] = self.create_publisher(Float64, f"{base}/value", STATE_QOS)
        self.cmd_sub.append(self.create_subscription(
            String, f"{base}/command", lambda m, n=name: self._send(n, m.data), 10))
        self._publish(name, data.get("state"))
        return True

    def _add_ros_input(self, entry):
        try:
            m = parse_mapping(entry)
            pkg, _, cls = m["msg_type"].replace("/msg/", "/").partition("/")
            msg_cls = getattr(importlib.import_module(f"{pkg}.msg"), cls)
        except (ValueError, ImportError, AttributeError) as e:
            self.get_logger().error(f"ros_inputs '{entry}': {e}")
            return
        item, update = m["item"], m["mode"] == "update"

        def callback(msg):
            value = getattr(msg, "data", None)
            if value is None:
                self.get_logger().warn(f"{m['topic']}: message has no 'data' field")
                return
            item_type = self.types.get(item, ("String", ""))[0]
            self._send(item, to_openhab(value, item_type), update)

        self.cmd_sub.append(self.create_subscription(msg_cls, m["topic"], callback, 10))
        self.get_logger().info(f"{m['topic']} -> {item} ({m['mode']})")

    # ------------------------------------------------------------------ openHAB -> ROS
    def _make_state(self, name, state):
        item_type, group_type = self.types.get(name, ("String", ""))
        msg = ItemState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "openhab"
        msg.name, msg.type, msg.state = name, item_type, "" if state is None else str(state)
        parsed = parse_state(msg.state, item_type, group_type)
        msg.is_null, msg.has_number = parsed["is_null"], parsed["has_number"]
        msg.number, msg.unit, msg.values = parsed["number"], parsed["unit"], parsed["values"]
        return msg

    def _publish(self, name, state):
        if name not in self.state_pub:
            return
        msg = self._make_state(name, state)
        self.state_pub[name].publish(msg)  # publish() may be called from any thread
        if msg.has_number and name in self.value_pub:
            self.value_pub[name].publish(Float64(data=msg.number))

    def _read_events(self):
        events = ItemEvents(self.client)
        while not self._stop.is_set() and rclpy.ok():
            stream = events.ItemStateChangedEvent()
            if _error(stream):
                self._set_connected(False, _error(stream))
                self._stop.wait(self.reconnect_delay)
                continue
            self._set_connected(True)
            self._republish_all()  # changes during a disconnect are not lost
            try:
                for event in iterSSEEvents(stream):
                    name = event["topic"].split("/")[2]
                    if name in self.state_pub:
                        self.counters["events"] += 1
                        self._publish(name, event["payload"].get("value"))
            except Exception as e:  # stream closed, network error, shutdown
                if self._stop.is_set():
                    return
                self.get_logger().warn(f"event stream interrupted: {e}")
            self._set_connected(False, "event stream ended")
            self._stop.wait(self.reconnect_delay)

    def _republish_all(self):
        for name in self.state_pub:
            state = self.items_api.getItemState(name)
            if not _error(state):
                self._publish(name, state)

    def _set_connected(self, ok, reason=""):
        # rclpy allows only one severity per call site – hence two separate calls
        if ok and not self.connected:
            self.get_logger().info("connected to openHAB")
        elif not ok and self.connected:
            self.get_logger().warn(f"openHAB not reachable: {reason}")
        self.connected = ok

    # ------------------------------------------------------------------ ROS -> openHAB
    def _send(self, name, command, update=False):
        api = self.items_api.postUpdate if update else self.items_api.sendCommand
        result = api(name, command, self.source)
        if _error(result):
            self.counters["errors"] += 1
            self.get_logger().error(f"{name} <- {command}: {_error(result)}")
            return False, _error(result)
        self.counters["updates" if update else "commands"] += 1
        self.get_logger().info(f"{name} <- {command}" + (" (update)" if update else ""))
        return True, "OK"

    def _on_item_command(self, msg):
        self._send(msg.name, msg.command, msg.update)

    def _srv_send_command(self, request, response):
        response.success, response.message = self._send(request.name, request.command,
                                                         request.update)
        return response

    def _srv_get_item(self, request, response):
        data = self.items_api.getItem(request.name, metadata="")
        if _error(data):
            response.success, response.message = False, _error(data)
            return response
        self.types.setdefault(request.name, (data.get("type", "String"),
                                             data.get("groupType", "")))
        response.item = self._make_state(request.name, data.get("state"))
        response.success, response.message = True, "OK"
        return response

    def _srv_list_items(self, request, response):
        data = self.items_api.getItems(type=request.type or None, tags=request.tags or None,
                                       fields="name,type,label")
        if _error(data):
            response.success, response.message = False, _error(data)
            return response
        for item in sorted(data, key=lambda i: i["name"]):
            response.names.append(item["name"])
            response.types.append(item.get("type", ""))
            response.labels.append(item.get("label", "") or "")
            response.bridged.append(item["name"] in self.state_pub)
        response.success, response.message = True, f"{len(data)} items"
        return response

    # ------------------------------------------------------------------ diagnostics
    def _publish_diagnostics(self):
        status = DiagnosticStatus(name="openhab_bridge", hardware_id=self.url)
        status.level = DiagnosticStatus.OK if self.connected else DiagnosticStatus.ERROR
        status.message = "connected" if self.connected else "openHAB not reachable"
        status.values = [KeyValue(key="items", value=str(len(self.state_pub)))] + [
            KeyValue(key=k, value=str(v)) for k, v in self.counters.items()]
        array = DiagnosticArray(status=[status])
        array.header.stamp = self.get_clock().now().to_msg()
        self.diag_pub.publish(array)

    def destroy_node(self):
        self._stop.set()  # the reader is a daemon thread and ends with the process
        return super().destroy_node()


def clean(values):
    """ROS 2 cannot declare an empty string array – [""] stands for "nothing"."""
    return [v for v in (values or []) if v]


def main(args=None):
    rclpy.init(args=args)
    node = OpenHABBridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl+C or 'ros2 launch' stopping the node
    finally:
        try:
            node.destroy_node()
            rclpy.try_shutdown()
        except KeyboardInterrupt:  # a second Ctrl+C while shutting down
            pass


if __name__ == "__main__":
    main()
