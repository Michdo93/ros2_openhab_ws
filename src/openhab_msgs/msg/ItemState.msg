# State of one openHAB item, published by the bridge on
#   /openhab/items/<name>/state   (QoS: reliable, transient local, depth 1)
std_msgs/Header header
string name        # item name, e.g. Livingroom_Light
string type        # item type, e.g. Switch, Dimmer, Number:Temperature, Group
string state       # state exactly as openHAB reports it, e.g. ON, 42, 21.5 °C, 120,100,50
bool is_null       # true for NULL and UNDEF
bool has_number    # true if "number" holds a valid value
float64 number     # Switch/Contact: 1 or 0, Dimmer/Rollershutter: percent,
                   # Number: value without unit, Color: brightness, DateTime: Unix time in s
string unit        # unit of a Number:<Dimension> item, e.g. °C, W, %
float64[] values   # Color: hue, saturation, brightness;
                   # Location: latitude, longitude, altitude
