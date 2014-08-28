from json import JSONEncoder, JSONDecoder


class MessageEncoder(JSONEncoder):
    pass


class MessageDecoder(JSONDecoder):
    pass


class Message(dict):
    decoder = MessageDecoder()
    encoder = MessageEncoder()

    def encode(self):
        return self.encoder.encode(self).encode("utf-8")


    @classmethod
    def decode(cls, s):
        try:
            s.decode
        except AttributeError:
            s = cls.join_frames(s)
        return cls(self.decoder.decode(s.decode("utf-8")))


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
    def create_router_message(cls, identity, request):
        m = identity[:]
        m.append(b'')
        m.append(cls.encode(request))
        return m


    @classmethod
    def join_frames(cls, frames):
        return b''.join(frames)



split_router_message = Message.split_router_message
join_frames = Message.join_frames
create_router_message = Message.create_router_message
