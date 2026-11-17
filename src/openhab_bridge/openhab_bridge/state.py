"""Conversion between openHAB states and plain values – no ROS dependency, unit-tested."""
import re
from datetime import datetime

NULL_STATES = ("NULL", "UNDEF")
_NUMBER = re.compile(r"^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(.*?)\s*$")
_ON_OFF = {"ON": 1.0, "OFF": 0.0, "OPEN": 1.0, "CLOSED": 0.0,
           "PLAY": 1.0, "PAUSE": 0.0, "UP": 0.0, "DOWN": 100.0}


def base_type(item_type: str, group_type: str = "") -> str:
    """'Number:Temperature' -> 'Number'; a group with a base type behaves like that type."""
    if item_type == "Group" and group_type:
        item_type = group_type
    return (item_type or "String").split(":")[0]


def parse_state(state: str, item_type: str = "String", group_type: str = "") -> dict:
    """Split an openHAB state into number, unit and values.

    Returns a dict with the keys is_null, has_number, number, unit, values.
    """
    out = {"is_null": False, "has_number": False, "number": 0.0, "unit": "", "values": []}
    state = "" if state is None else str(state)
    if state in NULL_STATES or state == "":
        out["is_null"] = True
        return out
    kind = base_type(item_type, group_type)
    if kind in ("Switch", "Contact", "Player") or state in _ON_OFF and kind == "Rollershutter":
        if state in _ON_OFF:
            out.update(has_number=True, number=_ON_OFF[state])
        return out
    if kind in ("Color", "Location"):
        try:
            values = [float(v) for v in state.split(",")]
        except ValueError:
            return out
        out["values"] = values
        if kind == "Color" and len(values) == 3:
            out.update(has_number=True, number=values[2])
        return out
    if kind == "DateTime":
        try:
            out.update(has_number=True, number=datetime.fromisoformat(state).timestamp())
        except ValueError:
            pass
        return out
    m = _NUMBER.match(state)
    if m and kind in ("Number", "Dimmer", "Rollershutter", "String"):
        out.update(has_number=True, number=float(m.group(1)), unit=m.group(2))
    return out


def to_openhab(value, item_type: str = "String") -> str:
    """Convert a ROS value (bool, int, float, str) to a command/state string for an item."""
    kind = base_type(item_type)
    if isinstance(value, bool):
        if kind == "Contact":
            return "OPEN" if value else "CLOSED"
        if kind in ("Dimmer", "Rollershutter", "Number"):
            return "100" if value else "0"
        return "ON" if value else "OFF"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def parse_mapping(entry: str) -> dict:
    """Parse 'topic|msg_type|item|mode' (mode: command or update, default update)."""
    parts = [p.strip() for p in entry.split("|")]
    if len(parts) not in (3, 4) or not all(parts[:3]):
        raise ValueError(f"expected 'topic|msg_type|item[|command|update]', got {entry!r}")
    mode = parts[3] if len(parts) == 4 and parts[3] else "update"
    if mode not in ("command", "update"):
        raise ValueError(f"mode must be 'command' or 'update', got {mode!r}")
    return {"topic": parts[0], "msg_type": parts[1], "item": parts[2], "mode": mode}
