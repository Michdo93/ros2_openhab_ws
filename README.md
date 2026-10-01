# ROS2 openHAB Integration

ROS2 Jazzy workspace for integrating openHAB with ROS2.  
Uses [`python-openhab-rest-client`](https://github.com/Michdo93/python-openhab-rest-client) for REST and SSE communication.

---

## Package Overview

| Package | Description |
|---|---|
| `openhab_msgs` | `.msg` and `.srv` definitions for all openHAB item types |
| `openhab_rest` | Service server nodes: GetState + SendCommand via REST API |
| `openhab_events` | Publisher nodes: streams state changes via SSE (ItemStateChangedEvent) |
| `openhab_static_examples` | Fixed example Subscriber + Client nodes per item type |
| `openhab_cmd` | Generic CLI nodes: any item by parameter at runtime |

---

## Architecture

```
openHAB Server
    │
    │  REST API (HTTP)
    │◄─────────────────────────  openhab_rest_server
    │                                 │ GetState / SendCommand
    │                                 │ ROS2 Services
    │                            ROS2 Service Clients
    │
    │  SSE (ItemStateChangedEvent)
    │─────────────────────────►  openhab_event_publisher
    │                                 │ /openhab/state/<ItemName>
    │                                 │ ROS2 Topics (typed msgs)
    │                            ROS2 Subscribers
    │
    │  REST API (sendCommand)
    │◄─────────────────────────  openhab_cmd_bridge_subscriber
                                      │ /openhab/command/<ItemName>
                                      │ ROS2 Topics (Command msgs)
                                 ROS2 Publishers
```

### Data flows

**Get state (one-shot):**
```
Client Node → Service Request (/openhab/get_state/<type>)
           → openhab_rest_server → REST GET /rest/items/<n>/state
           → Service Response with typed state message
```

**Send command (one-shot):**
```
Client Node → Service Request (/openhab/send_command/<type>)
           → openhab_rest_server → REST POST /rest/items/<n>
           → Service Response (success/message)
```

**SSE event stream (continuous, push from openHAB):**
```
openHAB item changes
   → SSE ItemStateChangedEvent
   → openhab_event_publisher
   → /openhab/state/<ItemName>  [typed *State msg]
   → Your subscriber node
```

**Continuous command push (ROS2 → openHAB):**
```
Your publisher node
   → /openhab/command/<ItemName>  [typed *Command msg]
   → openhab_cmd_bridge_subscriber
   → REST POST /rest/items/<n>
   → openHAB executes command
```

---

## Supported Item Types

| openHAB Type | State Message | Command Message | GetState Service | SendCommand Service |
|---|---|---|---|---|
| Call | `CallState` | – | `GetCallState` | – |
| Color | `ColorState` | `ColorCommand` | `GetColorState` | `SendColorCommand` |
| Contact | `ContactState` | `ContactCommand` | `GetContactState` | `SendContactCommand` |
| DateTime | `DateTimeState` | `DateTimeCommand` | `GetDateTimeState` | `SendDateTimeCommand` |
| Dimmer | `DimmerState` | `DimmerCommand` | `GetDimmerState` | `SendDimmerCommand` |
| Image | `ImageState` | – | `GetImageState` | – |
| Location | `LocationState` | `LocationCommand` | `GetLocationState` | `SendLocationCommand` |
| Number | `NumberState` | `NumberCommand` | `GetNumberState` | `SendNumberCommand` |
| Player | `PlayerState` | `PlayerCommand` | `GetPlayerState` | `SendPlayerCommand` |
| Rollershutter | `RollershutterState` | `RollershutterCommand` | `GetRollershutterState` | `SendRollershutterCommand` |
| String | `StringState` | `StringCommand` | `GetStringState` | `SendStringCommand` |
| Switch | `SwitchState` | `SwitchCommand` | `GetSwitchState` | `SendSwitchCommand` |

---

## Installation

### Dependencies

```bash
# ROS2 Jazzy base
sudo apt install ros-jazzy-rclcpp ros-jazzy-rclpy

# Build tools
sudo apt install libcurl4-openssl-dev nlohmann-json3-dev

# Python openHAB REST client (latest from GitHub)
pip install python-openhab-rest-client
# or for the newest async version:
pip install git+https://github.com/Michdo93/python-openhab-rest-client.git
```

### Build

```bash
cd ~/ros2_openhab_ws
colcon build --symlink-install
source install/setup.bash
```

---

## Usage

### 1. Start the REST Service Server

```bash
# Python version
ros2 run openhab_rest openhab_rest_server.py \
    --ros-args \
    -p openhab_url:=http://192.168.1.100:8080 \
    -p openhab_token:=oh.openhab.YourTokenHere

# C++ version
ros2 run openhab_rest openhab_rest_server_cpp \
    --ros-args \
    -p openhab_url:=http://192.168.1.100:8080 \
    -p openhab_token:=oh.openhab.YourTokenHere

# With username/password instead of token
ros2 run openhab_rest openhab_rest_server.py \
    --ros-args \
    -p openhab_url:=http://192.168.1.100:8080 \
    -p openhab_user:=admin \
    -p openhab_password:=yourpassword
```

### 2. Start the SSE Event Publisher

```bash
# Python version
ros2 run openhab_events openhab_event_publisher.py \
    --ros-args \
    -p openhab_url:=http://192.168.1.100:8080 \
    -p openhab_token:=oh.openhab.YourTokenHere \
    -p item_type_map:='{"LivingRoomLight":"Switch","Dimmer1":"Dimmer","Temp1":"Number","Color1":"Color"}'

# C++ version
ros2 run openhab_events openhab_event_publisher_cpp \
    --ros-args \
    -p openhab_url:=http://192.168.1.100:8080 \
    -p openhab_token:=oh.openhab.YourTokenHere \
    -p item_type_map:='{"LivingRoomLight":"Switch","Dimmer1":"Dimmer"}'
```

### 3. Query a state (generic)

```bash
# Get Switch state
ros2 run openhab_cmd openhab_get_state.py \
    --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch

# Get Number state
ros2 run openhab_cmd openhab_get_state.py \
    --ros-args -p item_name:=RoomTemperature -p item_type:=Number

# Get Color state
ros2 run openhab_cmd openhab_get_state.py \
    --ros-args -p item_name:=LivingRoomColor -p item_type:=Color
```

### 4. Send a command (generic)

```bash
# Switch ON
ros2 run openhab_cmd openhab_send_command.py \
    --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch -p command:=ON

# Dimmer to 75%
ros2 run openhab_cmd openhab_send_command.py \
    --ros-args -p item_name:=LivingRoomDimmer -p item_type:=Dimmer -p command:=75

# Color (HSB)
ros2 run openhab_cmd openhab_send_command.py \
    --ros-args -p item_name:=LivingRoomColor -p item_type:=Color -p command:="120.0,100.0,100.0"

# Rollershutter UP
ros2 run openhab_cmd openhab_send_command.py \
    --ros-args -p item_name:=BedroomBlind -p item_type:=Rollershutter -p command:=UP

# Player PLAY
ros2 run openhab_cmd openhab_send_command.py \
    --ros-args -p item_name:=RadioPlayer -p item_type:=Player -p command:=PLAY
```

### 5. Subscribe to state changes (generic)

```bash
# Subscribe to a Switch item
ros2 run openhab_cmd openhab_subscriber.py \
    --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch

# Subscribe to a Number item
ros2 run openhab_cmd openhab_subscriber.py \
    --ros-args -p item_name:=RoomTemperature -p item_type:=Number
```

### 6. Publish commands to openHAB (push pipeline)

Start the bridge subscriber (reads from ROS2 topic, sends to openHAB):
```bash
ros2 run openhab_cmd openhab_cmd_bridge_subscriber.py \
    --ros-args \
    -p item_name:=LivingRoomLight \
    -p item_type:=Switch \
    -p openhab_url:=http://192.168.1.100:8080 \
    -p openhab_token:=oh.openhab.YourTokenHere
```

Then publish a command:
```bash
# One-shot
ros2 run openhab_cmd openhab_publisher.py \
    --ros-args -p item_name:=LivingRoomLight -p item_type:=Switch -p command:=ON

# Continuous at 0.2 Hz
ros2 run openhab_cmd openhab_publisher.py \
    --ros-args \
    -p item_name:=LivingRoomLight \
    -p item_type:=Switch \
    -p command:=ON \
    -p publish_once:=false \
    -p rate_hz:=0.2
```

### 7. Static example nodes

```bash
# Fixed subscriber examples (templates)
ros2 run openhab_static_examples switch_subscriber.py
ros2 run openhab_static_examples dimmer_subscriber.py
ros2 run openhab_static_examples color_subscriber.py
ros2 run openhab_static_examples number_subscriber.py
# ... etc for all item types

# Fixed GetState client examples
ros2 run openhab_static_examples switch_get_state_client.py
ros2 run openhab_static_examples number_get_state_client.py

# Fixed SendCommand client examples
ros2 run openhab_static_examples switch_send_command_client.py
ros2 run openhab_static_examples dimmer_send_command_client.py
```

---

## Service and Topic Reference

### ROS2 Services (provided by `openhab_rest_server`)

| Service | Type | Description |
|---|---|---|
| `/openhab/get_state/call` | `GetCallState` | Get Call item state |
| `/openhab/get_state/color` | `GetColorState` | Get Color item state |
| `/openhab/get_state/contact` | `GetContactState` | Get Contact item state |
| `/openhab/get_state/datetime` | `GetDateTimeState` | Get DateTime item state |
| `/openhab/get_state/dimmer` | `GetDimmerState` | Get Dimmer item state |
| `/openhab/get_state/image` | `GetImageState` | Get Image item state |
| `/openhab/get_state/location` | `GetLocationState` | Get Location item state |
| `/openhab/get_state/number` | `GetNumberState` | Get Number item state |
| `/openhab/get_state/player` | `GetPlayerState` | Get Player item state |
| `/openhab/get_state/rollershutter` | `GetRollershutterState` | Get Rollershutter state |
| `/openhab/get_state/string` | `GetStringState` | Get String item state |
| `/openhab/get_state/switch` | `GetSwitchState` | Get Switch item state |
| `/openhab/send_command/color` | `SendColorCommand` | Send Color command |
| `/openhab/send_command/contact` | `SendContactCommand` | Send Contact command |
| `/openhab/send_command/datetime` | `SendDateTimeCommand` | Send DateTime command |
| `/openhab/send_command/dimmer` | `SendDimmerCommand` | Send Dimmer command |
| `/openhab/send_command/location` | `SendLocationCommand` | Send Location command |
| `/openhab/send_command/number` | `SendNumberCommand` | Send Number command |
| `/openhab/send_command/player` | `SendPlayerCommand` | Send Player command |
| `/openhab/send_command/rollershutter` | `SendRollershutterCommand` | Send Rollershutter command |
| `/openhab/send_command/string` | `SendStringCommand` | Send String command |
| `/openhab/send_command/switch` | `SendSwitchCommand` | Send Switch command |

### ROS2 Topics

| Topic | Direction | Type | Description |
|---|---|---|---|
| `/openhab/state/<ItemName>` | openHAB → ROS2 | `*State` | State from SSE event publisher |
| `/openhab/command/<ItemName>` | ROS2 → openHAB | `*Command` | Commands forwarded to openHAB REST |

---

## Color Item Note

openHAB Color items use **HSB** (Hue, Saturation, Brightness) both for state
and commands, e.g. `"120.0,100.0,100.0"` for full green.
The `ColorState` and `ColorCommand` messages carry all three float fields
as well as the raw state string.

---

## License

MIT
