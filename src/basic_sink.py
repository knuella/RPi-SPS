import zmq



def main():
    context = zmq.Context.instance()
    sub = context.socket(zmq.SUB)
    sub.set_string(zmq.SUBSCRIBE, "weather")
    sub.connect("tcp://127.0.0.10:5555")

    m = sub.recv_multipart()
    print(m)


while True:
    main()
