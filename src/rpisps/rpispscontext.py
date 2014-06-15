# TODO: error handling!
import time
import json
import argparse

import zmq

from rpisps.constants import *


class Message(dict):
    def encode(self):
        return json.dumps(self).encode("utf-8")

    @classmethod
    def decode(cls, s):
        # TODO: catch TypeError
        return cls(json.loads(s.decode("utf-8")))



class RpispsContext():
    def __init__(self):
        self._config = self._get_config()
        config = self._config

        self._context = zmq.Context.instance()
        c = self._context

        self._requests = c.socket(zmq.REQ)
        self._requests.connect(config.request_address)

        self._services = c.socket(zmq.ROUTER)
        self._services.connect(config.service_address)

        # new values are pushed to here
        self._submit_values = c.socket(zmq.PUSH)
        self._submit_values.connect(config.submit_values_address)

        # value updates come in here
        self._new_values = c.socket(zmq.SUB)
        self._new_values.connect(config.new_values_address)


    def _get_config(self):
        parser = argparse.ArgumentParser()

        parser.add_argument("name")
        parser.add_argument("service_address")
        parser.add_argument("request_address")
        parser.add_argument("new_values_address")
        parser.add_argument("submit_values_address")

        return parser.parse_args()


    def publish(self, payload):
        m = Message({
            "from": self._config.name,
            "timestamp": time.time(),
            "payload": payload,
        })

        self._submit_values.send_multipart([
            self._config.name.encode("utf-8"),
            m.encode()
        ])


    def request_value(self, name, payload=None):
        m = Message({
            "type": "RequestValue",
            "dst": name,
            "from": self._config.name,
        })

        if payload:
            m["payload"] = payload

        self._requests.send(m.encode())
        reply = self._requests.recv()
        return Message.decode(reply)


    def write_value(self, name, value):
        m = Message({
            "type": "WriteValue",
            "dst": name,
            "from": self._config.name,
            "payload": value
        })

        self._requests.send(m.encode())
        reply = self._requests.recv()
        return Message.decode(reply)


    def recv_updates(self):
        raw = self._new_values.recv_multipart()
        m = Message.decode(b''.join(raw[1:]))
        return m


    def recv_request(self):
        raw = self._services.recv_multipart()
        m = Message.decode(raw[2:])
        return m


    def send_reply(dst, payload, **extra):
        m = Message({
            "type": "Reply",
            "timestamp": extra.get("timestamp", time.time()),
            "status": extra.get("status", 0),
            "from": self._config.name,
            "dst": dst,
            "payload": payload
        })
        self._services.send_multipart([
            CONTROLLER_IDENTITY,
            b'',
            m.encode()
        ])


    def set_subscriptions(self, names):
        for n in names:
            self._new_values.set_string(zmq.SUBSCRIBE, n)


    def remove_subscriptions(self, names):
        for n in names:
            self._new_values.set_string(zmq.UNSUBSCRIBE, n)


    def make_source_known(self):
        self.send_reply("NONE", status=SERIVCE_HELLO)
