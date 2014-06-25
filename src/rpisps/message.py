import json


class Message(dict):
    def encode(self):
        return json.dumps(self).encode("utf-8")

    @classmethod
    def decode(cls, s):
        try:
            s.decode
        except AttributeError:
            s = cls.join_frames(s)
        return cls(json.loads(s.decode("utf-8")))


    @classmethod
    def split_router_message(cls, raw_message):
        # should use something like "rindex", right now it finds the
        # first occurence of b''
        last_empty_frame_pos = raw_message.index(b'')

        identity = raw_message[:last_empty_frame_pos]
        raw_request = raw_message[last_empty_frame_pos+1:]

        request = cls.decode(raw_request)

        return (identity, request)
        pass


    @classmethod
    def join_frames(cls, frames):
        return b''.join(frames)



split_router_message = Message.split_router_message
join_frames = Message.join_frames
