#!/usr/bin/python


class RpispsException(Exception):
    def __init__(self, message="Unspecified Error"):
        super().__init__()
        self.message = message


class DatabaseError(RpispsException):
    pass


class MessageFormatError(RpispsException):
    pass


class UnsupportedOperation(RpispsException):
    pass


class NoConnectionError(RpispsException):
    pass


class ExclusiveBlockError(RpispsException):
    pass
