import json
import logging
import threading
import argparse
import textwrap
import configparser
import sys

from threading import Thread
from time import sleep
from collections import deque

import zmq
from rpisps.constants import *



logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
message_list = []

def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="./controller.conf",
                        help="Path to a configuration file")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    try:
        with open(args.config, "r") as config_file:
            config.read_file(config_file)
    except (FileNotFoundError, PermissionError):
        sys.exit("Could not open file '{}'".format(args.config))

    return config["controller"]


def is_valid_publisher_message(message):
    """
    Returns True when the message format appears to be valid.

    A message is considered valid when its first frame is a string and
    the others are, concatenated, valid JSON.
    """
    return True


def is_valid_request(message):
    # should do some sanity checking on request messages
    return True


def split_request_message(message):
    """
    Returns a tuple (identity, JSON)
    """
    identity = message[0]
    raw_request = message[message.index(b''):]

    return (identity, raw_request)


def decode_message(message):
    try:
        return json.loads(b''.join(message).decode("utf-8"))
    except TypeError:
        return json.loads(message.decode("utf-8"))


def encode_message(message):
    return json.dumps(message).encode("utf-8")



class ServicesRequestsBaseThread(Thread):
    def __init__(self, context, terminate, router_address, **kwargs):
        super().__init__(**kwargs)

        self.terminate = terminate

        self.router = context.socket(zmq.ROUTER)
        self.router.setsockopt(zmq.IDENTITY, CONTROLLER_IDENTITY)
        self.router.bind(router_address)

        self.other_thread = context.socket(zmq.PAIR)
        try:
            self.other_thread.bind("inproc://services_requests")
        except zmq.error.ZMQError as e:
            if e.errno == zmq.EADDRINUSE:
                self.other_thread.connect("inproc://services_requests")
            else:
                raise

        self.poller = zmq.Poller()
        self.poller.register(self.router, flags=zmq.POLLIN)
        self.poller.register(self.other_thread, flags=zmq.POLLIN)


    def run(self):
        while not self.terminate.is_set():
            try:
                ready_sockets = self.poller.poll(timeout=1000)
                if self.can_handle_request(ready_sockets):
                    self.handle_request()
                if self.can_handle_reply(ready_sockets):
                    self.handle_reply()
            except (KeyboardInterrupt, SystemExit):
                self.terminate.set()

        logging.debug("terminating %s", self.name)


    def handle_request(self):
        raise NotImplementedError


    def handle_reply(self):
        raise NotImplementedError


    def can_handle_request(self, poll_result):
        raise NotImplementedError


    def can_handle_reply(self, poll_result):
        raise NotImplementedError


    def can_handle_reply(self, poll_result):
        raise NotImplementedError


    def can_pass_to_router(self, poll_result):
        for s, result in poll_result:
            if s is self.other_thread:
                router_result = self.router.poll(timeout=0, flags=zmq.POLLOUT)
                if router_result:
                    return result & zmq.POLLIN
        return False


    def can_pass_to_other(self, poll_result):
        for s, result in poll_result:
            if s is self.router:
                other_result = self.other_thread.poll(timeout=0, flags=zmq.POLLOUT)
                if other_result:
                    return result & zmq.POLLIN
        return False


    def get_socket_result(self, socket, poll_result):
        for s, r in poll_result:
            if s is socket:
                return r
        return 0


    def split_router_message(self, raw_message):
        raise NotImplementedError



class RequestsThread(ServicesRequestsBaseThread):
    def __init__(self, context, terminate, requests_address, **kwargs):
        super().__init__(context, terminate, requests_address, **kwargs)

        self.services = self.other_thread
        self.requests = self.router

        # maps name of requester to zmq socket identity
        self.pending_requests = {}


    def handle_request(self):
        logging.debug("%s handle_request called",
                      self.__class__.__name__)
        full_request = self.requests.recv_multipart()
        identity, raw_request = split_request_message(full_request)
        message = decode_message(raw_request)
        logging.debug("%s received message: %s",
                      self.__class__.__name__, message)

        if is_valid_request(message):
            self.pending_requests[message["from"]] = identity
            self.services.send_multipart(raw_request)
        else:
            self.reply_invalid_request(identity, raw_request)


    def handle_reply(self):
        logging.debug("%s handle_reply called",
                      self.__class__.__name__)
        raw_reply = self.services.recv_multipart()
        message = decode_message(raw_reply)
        logging.debug("%s reply message is: %s",
                      self.__class__.__name__, message)
        if message['dst'] in self.pending_requests:
            reply = [self.pending_requests[message['dst']],
                     b'']
            reply.extend(raw_reply)
            self.requests.send_multipart(reply)
        # TODO: dropping replies to unkown dst silently for now


    can_handle_reply = ServicesRequestsBaseThread.can_pass_to_router

    can_handle_request = ServicesRequestsBaseThread.can_pass_to_other


    def reply_invalid_request(identity, raw_request):
        raise NotImplementedError



class ServicesThread(ServicesRequestsBaseThread):
    def __init__(self, context, terminate, services_address, **kwargs):
        super().__init__(context, terminate, services_address, **kwargs)

        self.services = self.router
        self.requests = self.other_thread

        # maps service name to identity
        self.services_ready = {}


    def handle_request(self):
        logging.debug("%s handle_request called",
                      self.__class__.__name__)
        raw_request = self.requests.recv_multipart()
        message = decode_message(raw_request)
        logging.debug("%s received %s",
                      self.__class__.__name__, message)
        if message["dst"] not in self.services_ready:
            # TODO: cache request for timeout time
            self.reply_unkown_service(message)
        else:
            request = [self.services_ready[message["dst"]], b'']
            request.extend(raw_request)
            self.services.send_multipart(request)


    def handle_reply(self):
        logging.debug("%s handle_reply called",
                      self.__class__.__name__)
        full_reply = self.services.recv_multipart()
        identity, raw_reply = split_request_message(full_reply)
        message = decode_message(raw_reply)
        logging.debug("%s reply is: %s", self.name, message)
        # overwrite previous entry
        self.services_ready[message["from"]] = identity
        if not message["status"] == SERVICE_HELLO:
            # handle unwanted replies in the RequestsThread
            self.requests.send_multipart(raw_reply)
        else:
            self.reply_service_hello(message)


    def reply_service_hello(self, message):
        reply = {
            "type": "Reply",
            "from": "controller",
            "dst": message["from"],
            "status": SERVICE_HELLO
        }
        raw_reply = [self.services_ready[reply["dst"]], b'',
                     encode_message(reply)]
        self.services.send_multipart(raw_reply)


    def reply_unkown_service(self, message):
        message = {
            "type": "Reply",
            "from": "controller",
            "dst": message["from"],
            "status": SERVICE_UNKNOWN
        }
        self.requests.send(encode_message(message))


    can_handle_reply = ServicesRequestsBaseThread.can_pass_to_other

    can_handle_request = ServicesRequestsBaseThread.can_pass_to_router



def get_value_updates(context, terminate, new_values_address):
     # clients connect to the pull to send new values to be published
    values = context.socket(zmq.PULL)
    values.bind(new_values_address)

    poll = zmq.Poller()
    poll.register(values, flags=zmq.POLLIN)

    # connects to a socket in the propagate_value_updates thread
    propagate = context.socket(zmq.PUSH)
    propagate.connect("inproc://propagate_values")

    while not terminate.is_set():
        try:
            if poll.poll(timeout=2000):
                new_value = values.recv_multipart()
                propagate.send_multipart(new_value)
        except (KeyboardInterrupt, SystemExit):
            terminate.set()

    logging.debug("terminating get_value_updates")


def propagate_value_updates(context, terminate, pub_address):
    # new messages are passed through from the get_value_updates thread
    values = context.socket(zmq.PULL)
    values.bind("inproc://propagate_values")

    poll = zmq.Poller()
    poll.register(values, flags=zmq.POLLIN)

    # clients connect to this socket to get informed about value changes
    pub = context.socket(zmq.PUB)
    pub.bind(pub_address)

    while not terminate.is_set():
        try:
            if poll.poll(timeout=2000):
                new_value = values.recv_multipart()
                if is_valid_publisher_message(new_value):
                    pub.send_multipart(new_value)
                else:
                    logging.error("%s is not a valid message to be published",
                                  new_value)
        except (KeyboardInterrupt, SystemExit):
            terminate.set()

    logging.debug("terminating propagate_value_updates")


def main():
    config = get_config()
    context = zmq.Context.instance()
    terminate = threading.Event()
    # set when the program is supposed to terminate
    # don't forget to set in case of e.g. a KeyboardInterrupt or
    # SystemExit exception in the thread and break out of it

    threads = [
        Thread(target=propagate_value_updates,
               args=[context, terminate, config["new_values_address"]],
               name="propagate_value_updates"),
        Thread(target=get_value_updates,
               args=[context, terminate, config["submit_values_address"]],
               name="get_value_updates"),
        RequestsThread(context, terminate, config["request_address"],
                       name="requests_thread"),
        ServicesThread(context, terminate, config["service_address"],
                       name="services_thread")
    ]

    for t in threads:
        t.start()

    while not terminate.is_set():
        try:
            sleep(5)
        except (KeyboardInterrupt, SystemExit):
            terminate.set()

    logging.debug("Collection threads")
    interrupted_again = False
    while threading.active_count() != 1:
        try:
            for t in threading.enumerate():
                if t is not threading.main_thread():
                    t.join(timeout=0.125)
                    if not t.is_alive():
                        logging.debug("Collected thread %s", t.name)
        except KeyboardInterrupt:
            if interrupted_again:
                break
            logging.info("Still collecting threads press C-c again to quit")
            interrupted_again = True


if __name__ == '__main__':
    main()
