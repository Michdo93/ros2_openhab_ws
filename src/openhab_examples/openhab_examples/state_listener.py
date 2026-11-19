"""Print every state the bridge publishes – finds the topics on its own.

ros2 run openhab_examples state_listener
"""

import rclpy
from openhab_msgs.msg import ItemState
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class StateListener(Node):
    def __init__(self):
        super().__init__("state_listener")
        self.subs = {}
        self.create_timer(2.0, self.discover)  # new items appear without a restart

    def discover(self):
        for topic, types in self.get_topic_names_and_types():
            if (
                topic.endswith("/state")
                and "openhab_msgs/msg/ItemState" in types
                and topic not in self.subs
            ):
                self.subs[topic] = self.create_subscription(
                    ItemState, topic, self.show, QOS
                )

    def show(self, m):
        extra = f"  -> {m.number:g} {m.unit}".rstrip() if m.has_number else ""
        self.get_logger().info(f"{m.name:<24} {m.type:<20} {m.state}{extra}")


def main(args=None):
    rclpy.init(args=args)
    node = StateListener()
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
