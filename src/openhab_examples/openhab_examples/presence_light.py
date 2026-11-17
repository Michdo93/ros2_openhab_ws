"""Motion sensor -> light, switched off again after a quiet period.

    ros2 run openhab_examples presence_light --ros-args -p motion:=Flur_Bewegung \
        -p light:=Flur_Licht -p timeout:=60.0
"""
import rclpy
from openhab_msgs.msg import ItemState
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                 durability=DurabilityPolicy.TRANSIENT_LOCAL)


class PresenceLight(Node):
    def __init__(self):
        super().__init__("presence_light")
        motion = self.declare_parameter("motion", "Flur_Bewegung").value
        light = self.declare_parameter("light", "Flur_Licht").value
        self.timeout = self.declare_parameter("timeout", 60.0).value
        self.command = self.create_publisher(String, f"/openhab/items/{light}/command", 10)
        self.create_subscription(ItemState, f"/openhab/items/{motion}/state", self.on_motion,
                                 QOS)
        self.timer = None

    def on_motion(self, m):
        if m.has_number and m.number > 0:  # ON or OPEN
            self.command.publish(String(data="ON"))
            if self.timer:
                self.timer.cancel()
            self.timer = self.create_timer(self.timeout, self.off)

    def off(self):
        self.timer.cancel()
        self.command.publish(String(data="OFF"))
        self.get_logger().info("no motion – light off")


def main(args=None):
    rclpy.init(args=args)
    node = PresenceLight()
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
