#!/usr/bin/python


class RpispsException(Exception):
    def __init__(self, message="Unspecified Error", *args):
        super().__init__(args)
        self.message = message


class DatabaseError(RpispsException):
    pass


class MessageFormatError(RpispsException):
    pass


class UnsupportedOperation(RpispsException):
    pass
