import sys
from datetime import datetime
from typing import Any, Dict
import zulip


DEBUG = False
LOCATIONS = {"60:C0:BF:48:1C:84": "4th floor", "60:C0:BF:46:F6:E6": "5th floor"}


def should_send_message(co2_level, location):
    # Don't send a message if the level is low enough
    if co2_level < 1000:
        print("CO2 levels are okay")
        return False

    stream = "397 Bridge"
    if DEBUG:
        stream = "bot-test"
    # Check if we've sent a message recently
    get_msg_req: Dict[str, Any] = {
        "anchor": "newest",
        "num_before": 100,
        "num_after": 0,
        "narrow": [
            {"operator": "sender", "operand": "co2bot-bot@recurse.zulipchat.com"},
            {"operator": "stream", "operand": stream},
            {"operator": "topic", "operand": f"CO2 level - {location}"},
        ],
    }
    msgs = client.get_messages(get_msg_req)
    timestamps = [m["timestamp"] for m in msgs["messages"]]

    # We've never sent a message yet, send a message
    if len(timestamps) == 0:
        print("Never sent a message before, sending a message")
        return True

    latest_message = max(timestamps)
    duration_since_last_message_min = (datetime.now().timestamp() - latest_message)/60

    # Don't send a message if we sent one <15 minutes ago
    if duration_since_last_message_min < 60:
        print("We already sent a message in the last 60 minutes, skipping")
        return False

    return True


def send_co2_message(co2_level, location):
    # Check if we've sent a message recently
    if not should_send_message(co2_level, location):
        return

    stream = "397 Bridge"
    if DEBUG:
        stream = "bot-test"

    request = {
        "type": "stream",
        "to": stream,
        "topic": f"CO2 level - {location}",
        "content": f"CO2 level on the {location} is currently {round(co2_level)}"
    }

    result = client.send_message(request)
    return result


def parse_single_reading(co2_string):
    reading = dict()
    for line in co2_string.splitlines():
        if ":" not in line:
            continue

        [k, value] = line.split(":", 1)
        reading[k.strip()] = value.strip()

    # TODO nicely parse the rest of the reading
    if "CO2" in reading:
        reading["CO2"] = float(reading["CO2"].split()[0])

    return reading


def parse_co2_string(co2_string):
    # Remove status messages
    lines = [l for l in co2_string.splitlines() if "Looking for" not in l and "Scan finished" not in l]

    co2_string = "\n".join(lines)
    readings = [parse_single_reading(s) for s in co2_string.split("=======================================")]

    levels = dict()
    for r in readings:
        if "Address" not in r:
            continue

        device_mac = r["Address"]
        if device_mac not in LOCATIONS:
            continue

        levels[LOCATIONS[device_mac]] = r["CO2"]

    return levels


if __name__ == "__main__":
    client = zulip.Client(config_file="~/.zuliprc")
    if not DEBUG:
        co2_string = sys.stdin.read()
    else:
        with open("scan.txt") as f:
            co2_string = f.read()

    co2_levels = parse_co2_string(co2_string)
    print(f"{len(co2_levels)} locations found")

    for location, level in co2_levels.items():
        print(f"\n{location}: {level} ppm CO2")
        send_co2_message(level, location)
