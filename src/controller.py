import json
import logging
import threading

from threading import Thread
from time import sleep
from collections import deque

import zmq


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
message_list = []

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
    raw_request = b''.join(message[message.index(b''):])
    request = json.loads(raw_request.decode("utf-8"))

    return (identity, request)


def invalid_request():
    return b'invalid request'


class RequestsThread(Thread):
    def __init__(self, context, terminate, **kwargs):
        super().__init__(**kwargs)

        self.terminate = terminate

        self.router = context.socket(zmq.ROUTER)
        # TODO: address should be read from config and passed in as a
        # parameter
        self.router.bind("tcp://127.0.0.10:6665")

        # connects to the thread handling services
        self.services = context.socket(zmq.PAIR)
        self.services.bind("inproc://services_requests")

        # maps name of requester to zmq socket identity
        self.pending_requests = {}

        self.poller = zmq.Poller()
        self.poller.register(self.router)
        self.poller.register(self.services)


    def _get_socket_result(self, socket, poll_result):
        for s, r in poll_result:
            if s is socket:
                return r
        return 0


    def can_handle_reply(self, poll_result):
        services_result = self._get_socket_result(self.services, poll_result)
        router_result = self._get_socket_result(self.router, poll_result)

        return ((services_result & zmq.POLLIN) and
                (router_result & zmq.POLLOUT))


    def can_handle_request(self, poll_result):
        services_result = self._get_socket_result(self.services, poll_result)
        router_result = self._get_socket_result(self.router, poll_result)

        return ((services_result & zmq.POLLOUT) and
                (router_result & zmq.POLLIN))


    def handle_request(self):
        raw_request = self.router.recv_multipart()
        if is_valid_request(message):
            self.services.send_multipart(raw_message)
        # TODO: dropping invalid messages silently for now


    def handle_reply(self):
        raw_reply = self.services.recv_multipart()
        self.router.send_multipart(raw_reply)


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



def get_value_updates(context, terminate):
     # clients connect to the pull to send new values to be published
    values = context.socket(zmq.PULL)
    values.bind("tcp://127.0.0.10:5556")

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


def propagate_value_updates(context, terminate):
    # new messages are passed through from the get_value_updates thread
    values = context.socket(zmq.PULL)
    values.bind("inproc://propagate_values")

    poll = zmq.Poller()
    poll.register(values, flags=zmq.POLLIN)

    # clients connect to this socket to get informed about value changes
    pub = context.socket(zmq.PUB)
    pub.bind("tcp://127.0.0.10:5555")

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
    context = zmq.Context.instance()
    terminate = threading.Event()
    # set when the program is supposed to terminate
    # don't forget to set in case of e.g. a KeyboardInterrupt or
    # SystemExit exception in the thread and break out of it

    threads = [
        Thread(target=propagate_value_updates, args=[context, terminate],
               name="propagate_value_updates"),
        Thread(target=get_value_updates, args=[context, terminate],
               name="get_value_updates"),
        RequestsThread(context, terminate, name="requests_thread")
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
