import json

import zmq

_SERVICE_HELLO = -1
_OK = 0


context = zmq.Context.instance()

request = context.socket(zmq.REQ)
request.connect("tcp://127.0.0.10:6665")

service = context.socket(zmq.REQ)
service.connect("tcp://127.0.0.10:6666")

service_message_hello = json.dumps({
    "type": "Reply",
    "dst": "test_request",
    "from": "test_service",
    "status": _SERVICE_HELLO
}).encode("utf-8")

service_message_reply = json.dumps({
    "type": "Reply",
    "dst": "test_request",
    "from": "test_service",
    "status": _OK
}).encode("utf-8")

request_message = json.dumps({
    "type": "RequestValue",
    "dst": "test_service",
    "from": "test_request"
}).encode("utf-8")


service.send(service_message_hello)
request.send(request_message)

print("Service Request: ", service.recv())
service.send(service_message_reply)

print("Request Reply: ", request.recv())
