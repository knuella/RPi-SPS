import json
import logging
import threading

from threading import Thread
from time import sleep

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


def get_requests(router):
    m = router.recv_multipart()
    logging.debug("FULL REQUEST: %s", m)
    try:
        identity, request = split_request_message(m)
    except ValueError:
        reply = [m[0], b'', invalid_request()]
        logging.debug("REPLY: %s", reply)
        router.send_multipart(reply)
    else:
        logging.debug("REQUEST: %s", request)


def get_value_updates(context, terminate):
     # clients connect to the pull to send new values to be published
    values = context.socket(zmq.PULL)
    values.bind("tcp://127.0.0.10:5556")

    poll = zmq.Poller()
    poll.register(values, flags=zmq.POLLIN)

    # connects to a socket in the propagate_value_updates thread
    propagate = context.socket(zmq.PUSH)
    propagate.connect("inproc://propagate_values")

    while not terminate.acquire(timeout=0):
        if poll.poll(timeout=2000):
            try:
                new_value = values.recv_multipart()
            except zmq.ZMQError:
                break
            except (KeyboardInterrupt, SystemExit):
                break
            else:
                propagate.send_multipart(new_value)

    logging.debug("terminating get_value_updates")
    terminate.release()


def propagate_value_updates(context, terminate):
    # new messages are passed through from the get_value_updates thread
    values = context.socket(zmq.PULL)
    values.bind("inproc://propagate_values")

    poll = zmq.Poller()
    poll.register(values, flags=zmq.POLLIN)

    # clients connect to this socket to get informed about value changes
    pub = context.socket(zmq.PUB)
    pub.bind("tcp://127.0.0.10:5555")

    while not terminate.acquire(timeout=0):
        if poll.poll(timeout=2000):
            try:
                new_value = values.recv_multipart()
            except zmq.ZMQError:
                break
            except (KeyboardInterrupt, SystemExit):
                break
            else:
                if is_valid_publisher_message(new_value):
                    pub.send_multipart(new_value)
                else:
                    logging.error("%s is not a valid message to be published",
                                  new_value)

    logging.debug("terminating propagate_value_updates")
    terminate.release()


def main():
    context = zmq.Context.instance()
    terminate = threading.Lock()
    # released when the program is supposed to terminate
    # check with "not termiante.acquire(timeout=0)"
    # and don't forget to release when the program is supposed to
    # quit, e.g. due to a KeyboardInterrupt or SystemExit exception in
    # the thread
    terminate.acquire()

    threads = [
        Thread(target=propagate_value_updates, args=[context, terminate],
               name="propagate_value_updates"),
        Thread(target=get_value_updates, args=[context, terminate],
               name="get_value_updates")
    ]

    for t in threads:
        t.start()

    while not terminate.acquire(timeout=0):
        try:
            sleep(5)
        except (KeyboardInterrupt, SystemExit):
            break
    terminate.release()

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
