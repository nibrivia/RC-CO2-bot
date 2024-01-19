import sys
import zulip


def send_co2_message(co2_level):
    client = zulip.Client(config_file="~/.zuliprc")

    # Send a stream message
    request = {
        "type": "stream",
        "to": "397 Bridge",
        "topic": "CO2 level",
        "content": f"CO2 level on the 4th floor is currently {co2_level}"
    }
    result = client.send_message(request)
    return result


def parse_co2_level(co2_string):
    return float(co2_string.split()[1])


if __name__ == "__main__":
    for line in sys.stdin:
        co2_line = line
        break

    co2_level = parse_co2_level(co2_line)
    print(co2_level)

    if co2_level > 900:
        send_co2_message(co2_level)
    else:
        print(f"CO2 level is low enough ({co2_level}), not sending a message")
