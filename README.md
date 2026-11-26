# ros2_openhab_ws – openHAB ↔ ROS 2 bridge

A ROS 2 workspace that connects [openHAB](https://www.openhab.org) items with the ROS 2 graph.
openHAB states become topics, ROS 2 topics and services become commands – in Python
([python-openhab-rest-client](https://github.com/Michdo93/python-openhab-rest-client)) and
C++ ([cpp-openhab-rest-client](https://github.com/Michdo93/cpp-openhab-rest-client)) with
identical topics and services.

Tested with ROS 2 **Lyrical Luth** (Ubuntu 26.04) and **Jazzy Jalisco** (Ubuntu 24.04,
Raspberry Pi 4/5) against openHAB 5.

> **Version 2** replaces the one-message-type-per-item-type design of version 1
> (`openhab_rest`, `openhab_events`, `openhab_cmd`, `openhab_static_examples`) with a single
> bridge node and one generic `ItemState` message. Version 1 remains in the git history.

## Packages

| Package | Content |
|---|---|
| `openhab_msgs` | `ItemState`, `ItemCommand`, services `GetItem`, `SendCommand`, `ListItems` |
| `openhab_bridge` | the bridge in Python (incl. `ros_inputs`: any ROS topic → item) |
| `openhab_bridge_cpp` | the same bridge in C++ |
| `openhab_examples` | `state_listener`, `presence_light`, a combined launch file |

## Topics and services

```
openHAB ──SSE──► openhab_bridge ──► /openhab/items/<Item>/state    openhab_msgs/ItemState
                                ──► /openhab/items/<Item>/value    std_msgs/Float64
openHAB ◄─REST── openhab_bridge ◄── /openhab/items/<Item>/command  std_msgs/String
                                ◄── /openhab/command               openhab_msgs/ItemCommand
                                ◄── ros_inputs (any topic with a 'data' field, Python only)
services: /openhab/get_item  /openhab/send_command  /openhab/list_items
status:   /diagnostics (diagnostic_msgs/DiagnosticArray, every 5 s)
```

* State topics use **reliable + transient local** QoS: a node that subscribes later still
  receives the last state at once. Subscribers must request the same durability.
* After a lost connection the bridge reconnects and publishes all states again, so no change
  is lost.
* `ItemState` carries the original state string plus a parsed `number` (Switch/Contact 1/0,
  Dimmer and Rollershutter in percent, Number without unit, DateTime as Unix time), the
  `unit` and `values` (Color: H, S, B; Location: latitude, longitude, altitude).

## Installation

```bash
sudo apt install python3-pip libcurl4-openssl-dev git
pip install --break-system-packages python-openhab-rest-client   # Python bridge
mkdir -p ~/ros2_ws && cd ~/ros2_ws
git clone https://github.com/Michdo93/ros2_openhab_ws.git src/ros2_openhab_ws
source /opt/ros/lyrical/setup.bash        # or jazzy
colcon build --symlink-install
source install/setup.bash
```

The C++ bridge uses an installed cpp-openhab-rest-client (`find_package`) or fetches it from
GitHub during the build. Skip it with `colcon build --packages-skip openhab_bridge_cpp`.

## Usage

Address and token come from the **environment**, never from parameters (every participant can
read parameters with `ros2 param get`):

```bash
export OPENHAB_URL=http://openhab:8080
export OPENHAB_TOKEN=oh.ros2.xxxxxxxx            # API token from the openHAB profile page
ros2 launch openhab_bridge bridge.launch.py params:=my_bridge.yaml
# or the C++ variant
ros2 launch openhab_bridge_cpp bridge.launch.py params:=my_bridge.yaml
```

`my_bridge.yaml`:

```yaml
openhab_bridge:
  ros__parameters:
    items: ["Wohnzimmer_Licht", "Kueche_Rollladen"]   # explicit items
    groups: ["gROS"]                                 # plus all members of these groups
    tags: [""]                                       # plus items with these tags
    namespace: openhab
    publish_value: true
    command_source: ros2
    reconnect_delay: 5.0
    # Python bridge only: "topic|msg_type|item[|command|update]"
    ros_inputs: ["/kinect/hand_detected|std_msgs/msg/Bool|Flur_Licht|command"]
```

`[""]` stands for an empty list (ROS 2 cannot declare an empty string array). If `items`,
`groups` and `tags` are all empty, every item is bridged.

```bash
ros2 topic echo /openhab/items/Wohnzimmer_Licht/state
ros2 topic pub --once /openhab/items/Wohnzimmer_Licht/command std_msgs/msg/String "{data: 'ON'}"
ros2 service call /openhab/send_command openhab_msgs/srv/SendCommand "{name: Wohnzimmer_Dimmer, command: '35'}"
ros2 service call /openhab/get_item openhab_msgs/srv/GetItem "{name: Kueche_Rollladen}"
ros2 service call /openhab/list_items openhab_msgs/srv/ListItems "{type: Switch}"
ros2 run openhab_examples state_listener
```

Quote `'ON'` and `'OFF'` in YAML – unquoted they are booleans and arrive as `True`/`False`.

## Tests

```bash
cd src/openhab_bridge && python3 -m pytest -q test     # state conversion, no openHAB needed
```

GitHub Actions builds all packages for Jazzy and Lyrical and runs the unit tests.

## Book

The bridge is described in detail in *Smart Home & ROS2 – Vernetzen Sie Ihr Zuhause wie einen
Roboter* by Michael Christian Dörflinger (Praxisreihe Smart Home).

## Support

If this repository helps you, you can buy the author a coffee:
https://buymeacoffee.com/Michdo93

## License

MIT
