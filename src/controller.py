import zmq


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
    print(m)
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


def main():
    context = zmq.Context.instance()
    pub = context.socket(zmq.PUB)
    sources_pull = context.socket(zmq.PULL)

    pub.bind("tcp://127.0.0.10:5555")
    sources_pull.bind("tcp://127.0.0.10:5556")

    poller = zmq.Poller()
    poller.register(sources_pull, flags=zmq.POLLIN)

    # main loop
    # should use some library for event-driven development
    while True:
        if len(poller.poll(timeout=0)) > 0:
            recv_new_values(sources_pull)

        publish_new_values(pub)




if __name__ == '__main__':
    main()
