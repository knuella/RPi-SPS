#!/usr/bin/python


class RpispsException(Exception):
    def __init__(self, message="Unspecified Error"):
        super().__init__()
        self.message = message


class DatabaseError(RpispsException):
    pass


class QueryFormatError(RpispsException):
    pass
