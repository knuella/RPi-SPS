from time import sleep

import zmq



context = zmq.Context.instance()
push = context.socket(zmq.PUSH)
push.connect("tcp://127.0.0.10:5556")

while True:
    push.send(b"dies ist ein test")
    sleep(5)
