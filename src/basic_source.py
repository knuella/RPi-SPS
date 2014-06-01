import time
import json

from time import sleep

import zmq


def get_config(name):
    # should make a request to config
    dummy_config = {
        "name": "weather",
        "source": "http://api.openweathermap.org/data/2.5/weather?q=Berlin,de",
        "params": ["source"]
    }

    return dummy_config


def publish_values(socket, name, values):
    payload = json.dumps(values, separators=(',',':'))
    socket.send_multipart(
        [
            name.encode("utf-8"),
            payload.encode("utf-8")
        ]
    )


def main():
    context = zmq.Context.instance()
    push = context.socket(zmq.PUSH)
    push.connect("tcp://127.0.0.10:5556") # should connect to sys.argv[2]

    config = get_config("weather") # should pass sys.argv[1]

    while True:
        payload = {
            "timestamp": time.time(),
            "payload": 5,
            "from": config["name"]
        }

        publish_values(push, config["name"], payload)
        sleep(5)


if __name__ == '__main__':
    main()
