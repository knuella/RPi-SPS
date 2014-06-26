import json
import logging
import threading
import argparse
import configparser
import sys

from threading import Thread
from time import sleep
from collections import deque

import zmq

from rpisps.constants import *
from rpisps.message import Message



logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)

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
        identity, message = Message.split_router_message(full_request)
        logging.debug("%s received message: %s",
                      self.__class__.__name__, message)

        if self.is_valid_request(message):
            self.pending_requests[message["from"]] = identity
            self.services.send(message.encode())
        else:
            self.reply_invalid_request(identity, message)


    def handle_reply(self):
        logging.debug("%s handle_reply called",
                      self.__class__.__name__)
        raw_reply = self.services.recv()
        message = Message.decode(raw_reply)
        logging.debug("%s reply message is: %s",
                      self.__class__.__name__, message)
        if message['dst'] in self.pending_requests:
            reply = self.pending_requests[message['dst']][:]
            reply.extend([b'', raw_reply])
            self.requests.send_multipart(reply)
        # TODO: dropping replies to unkown dst silently for now


    can_handle_reply = ServicesRequestsBaseThread.can_pass_to_router

    can_handle_request = ServicesRequestsBaseThread.can_pass_to_other


    def reply_invalid_request(identity, message):
        raise NotImplementedError


    def is_valid_request(self, message):
        # should do some sanity checking on request messages
        return True





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
        message = Message.decode(raw_request)
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
        identity, message = Message.split_router_message(full_reply)
        logging.debug("%s reply is: %s", self.name, message)
        # overwrite previous entry
        self.services_ready[message["from"]] = identity
        if not message["status"] == SERVICE_HELLO:
            # handle unwanted replies in the RequestsThread
            self.requests.send(message.encode())
        else:
            self.reply_service_hello(message)


    def reply_service_hello(self, message):
        reply = Message({
            "type": "Reply",
            "from": "controller",
            "dst": message["from"],
            "status": SERVICE_HELLO
        })
        raw_reply = self.services_ready[reply["dst"]][:]
        raw_reply.extend([b'', reply.encode()])
        self.services.send_multipart(raw_reply)


    def reply_unkown_service(self, message):
        reply = Message({
            "type": "Reply",
            "from": "controller",
            "dst": message["from"],
            "status": SERVICE_UNKNOWN
        })
        self.requests.send(message.encode())


    can_handle_reply = ServicesRequestsBaseThread.can_pass_to_other

    can_handle_request = ServicesRequestsBaseThread.can_pass_to_router



class PropagateValueUpdates(Thread):
    def __init__(self, context, terminate, pub_address, submit_values_address,
                 **kwargs):
        super().__init__(**kwargs)

        self.terminate = terminate

        self.new_values = context.socket(zmq.PULL)
        self.new_values.bind(submit_values_address)

        self.pub = context.socket(zmq.PUB)
        self.pub.bind(pub_address)


    def run(self):
        while not self.terminate.is_set():
            try:
                if self.new_values.poll(timeout=200, flags=zmq.POLLIN):
                    message = self.new_values.recv_multipart()
                    if self.is_valid_message(message):
                        self.pub.send_multipart(message)
            except (KeyboardInterrupt, SystemExit):
                terminate.set()

        logging.debug("terminating %s", self.name)


    def is_valid_message(self, message):
        return True



def main():
    config = get_config()
    context = zmq.Context.instance()
    terminate = threading.Event()
    # set when the program is supposed to terminate
    # don't forget to set in case of e.g. a KeyboardInterrupt or
    # SystemExit exception in the thread and break out of it

    threads = [
        PropagateValueUpdates(context, terminate,
                              config["new_values_address"],
                              config["submit_values_address"],
                              name="propagte_values_thread"),
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
