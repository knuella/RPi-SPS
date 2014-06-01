import json

import zmq


context = zmq.Context.instance()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.10:5557")

# socket.send(json.dumps("test").encode("utf-8"))
socket.send(b"test")
print(socket.recv_multipart())
