import pytest

from openhab_bridge.state import parse_mapping, parse_state, to_openhab


def test_switch_and_contact():
    assert parse_state("ON", "Switch")["number"] == 1.0
    assert parse_state("CLOSED", "Contact")["number"] == 0.0


def test_null_states():
    for s in ("NULL", "UNDEF", ""):
        assert parse_state(s, "Number")["is_null"]


def test_number_with_unit():
    r = parse_state("21.5 °C", "Number:Temperature")
    assert r["has_number"] and r["number"] == 21.5 and r["unit"] == "°C"


def test_dimmer_and_rollershutter():
    assert parse_state("40", "Dimmer")["number"] == 40.0
    assert parse_state("0", "Rollershutter")["number"] == 0.0


def test_color_and_location():
    c = parse_state("120,100,50", "Color")
    assert c["values"] == [120.0, 100.0, 50.0] and c["number"] == 50.0
    assert parse_state("48.05,8.2,700", "Location")["values"] == [48.05, 8.2, 700.0]


def test_group_with_base_type():
    assert parse_state("ON", "Group", "Switch")["number"] == 1.0


def test_datetime():
    r = parse_state("2026-11-17T20:13:00.000+0100", "DateTime")
    assert r["has_number"] and int(r["number"]) == 1794942780


def test_string_stays_string():
    assert not parse_state("Ladestation", "String")["has_number"]


def test_to_openhab():
    assert to_openhab(True, "Switch") == "ON"
    assert to_openhab(False, "Contact") == "CLOSED"
    assert to_openhab(0.5, "Number") == "0.5"
    assert to_openhab(42, "Dimmer") == "42"


def test_parse_mapping():
    m = parse_mapping("/kinect/hand|std_msgs/msg/Bool|Flur_Hand")
    assert m == {"topic": "/kinect/hand", "msg_type": "std_msgs/msg/Bool",
                 "item": "Flur_Hand", "mode": "update"}
    assert parse_mapping("/a|std_msgs/msg/Bool|X|command")["mode"] == "command"
    with pytest.raises(ValueError):
        parse_mapping("/a|X")
