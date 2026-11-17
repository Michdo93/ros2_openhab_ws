# Command (or state update) for an openHAB item, accepted on /openhab/command
string name        # item name
string command     # e.g. ON, OFF, 50, UP, 120,100,50
bool update        # false: send as command (default), true: post as state update
