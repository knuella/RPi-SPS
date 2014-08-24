# TODO: error handling!
import time
import json
import argparse

import zmq

from rpisps.message import Message
from rpisps.constants import *


class Context():
    def __init__(self, json_decoder=JSONDecoder(), json_encoder=JSONEncoder()):
        self._config = self._get_config()
        config = self._config

        Message.json_decoder = json_decoder
        Message.json_encoder = json_encoder

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
        m = Message.decode(raw[2])
        return m


    def send_reply(self, dst, payload=None, **extra):
        m = Message({
            "type": "Reply",
            "timestamp": extra.get("timestamp", time.time()),
            "status": extra.get("status", 0),
            "from": self._config.name,
            "dst": dst,
        })
        if payload:
            m["payload"] = payload

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
        poller = zmq.Poller()
        poller.register(self._services, flags=zmq.POLLIN)
        reply_received = False

        # wait for the _services connection to be build-up,
        # because the ROUTER socket brutally drops every message he
        # does not know how to deliver
        while not reply_received:
            self.send_reply("NONE", status=SERVICE_HELLO)
            if poller.poll(timeout=10):
                self._services.recv_multipart()
                reply_received = True
