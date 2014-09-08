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
        return cls(cls.decoder.decode(s.decode("utf-8")))


    @classmethod
    def split_router_message(cls, raw_message):
        """
        Splits the 'raw_message' into a pair (identity, request)

        Args:
            raw_message: List of zmq message frames.

        Returns:
            A tuple (identity, request)
        """
        # TODO: should use something like "rindex", right now it finds
        # the first occurence of b''
        last_empty_frame_pos = raw_message.index(b'')

        identity = raw_message[:last_empty_frame_pos]
        raw_request = raw_message[last_empty_frame_pos+1:]

        request = cls.decode(raw_request)

        return (identity, request)
        pass


    @classmethod
    def create_router_message(cls, identity, request):
        """
        Joins 'identity' and 'request' to create a router message

        Args:
            identity: List of frames representing identities understandable
                by an zmq.ROUTER.  The list should not contain a trailing
                empty frame (b'').
            request (Message): The message to send to the identity.

        Returns:
            A list that represents a message a zmq.ROUTER can send.
        """
        m = identity[:]
        m.append(b'')
        m.append(cls.encode(request))
        return m


    @classmethod
    def join_frames(cls, frames):
        """
        Return 'frames' concatenated as a single bytes object.
        """
        return b''.join(frames)



split_router_message = Message.split_router_message
join_frames = Message.join_frames
create_router_message = Message.create_router_message
