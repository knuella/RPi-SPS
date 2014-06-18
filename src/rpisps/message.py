import json


class Message(dict):
    def encode(self):
        return json.dumps(self).encode("utf-8")

    @classmethod
    def decode(cls, s):
        # TODO: catch TypeError
        return cls(json.loads(s.decode("utf-8")))
