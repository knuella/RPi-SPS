import zmq



def is_valid_publisher_message(message):
    """
    Returns True when the message format appears to be valid.

    A message is considered valid when its first frame is a string and
    the others are, concatenated, valid JSON.
    """
    return True


def recv_new_values(source, values_push):
    m = source.recv_multipart()
    if is_valid_publisher_message(m):
        message_list.append()
    # silently drop invalid messages for now


def publish_new_values(publisher, values_pull):
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

    pub.bind("tcp://localhost:5555")
    sources_pull.bind("tcp://localhost:5556")

    poller = zmq.Poller()
    poller.register(sources_pull)

    # main loop
    # should use some library for event-driven development
    while True:
        if poller.poll():
            recv_new_values(sources_pull)

        publish_new_values(pub)




if __name__ == '__main__':
    main()
