import zmq

context = zmq.Context.instance()
sub = context.socket(zmq.SUB)
sub.set_string(zmq.SUBSCRIBE, "dies")
sub.connect("tcp://127.0.0.10:5555")

while True:
    m = sub.recv_multipart()
    print(m)
