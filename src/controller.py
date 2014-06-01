import json
import logging

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


def recv_new_values(source):
    m = source.recv_multipart()
    logging.debug("NEW VALUE: %s", m)
    if is_valid_publisher_message(m):
        message_list.append(m)
    # silently drop invalid messages for now


def publish_new_values(publisher):
    try:
        m = message_list.pop()
    except IndexError:
        pass
    else:
        publisher.send_multipart(m)


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


def main():
    dispatch = {}

    context = zmq.Context.instance()
    pub = context.socket(zmq.PUB)
    sources_pull = context.socket(zmq.PULL)
    requests = context.socket(zmq.ROUTER)

    dispatch[pub] = publish_new_values
    dispatch[sources_pull] = recv_new_values
    dispatch[requests] = get_requests

    pub.bind("tcp://127.0.0.10:5555")
    sources_pull.bind("tcp://127.0.0.10:5556")
    requests.bind("tcp://127.0.0.10:5557")

    poller = zmq.Poller()
    poller.register(pub, flags=zmq.POLLOUT)
    poller.register(sources_pull, flags=zmq.POLLIN)
    poller.register(requests, flags=zmq.POLLIN)

    # main loop
    # should use some library for event-driven development
    while True:
        for socket, _ in poller.poll(timeout=0):
            dispatch[socket](socket)



if __name__ == '__main__':
    main()
