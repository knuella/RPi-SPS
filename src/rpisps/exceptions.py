#!/usr/bin/python
from rpisps.constants import *


class RpispsException(Exception):
    default_error = GENERIC_ERROR

    def __init__(self, message="Unspecified Error", *args, **kwargs):
        """
        Args:
          message (str): error message that will be returned to the requester
          args: gets passed to the base class exception

        Kwargs:
          errorcode (int): used for the status field of a message
        """
        super().__init__(args)
        self.message = message
        self.errorcode = kwargs.get("errorcode", self.default_error)


class DatabaseError(RpispsException):
    default_error = DATABASE_ERROR



class MessageFormatError(RpispsException):
    default_error = MESSAGE_ERROR


class UnsupportedOperation(RpispsException):
    default_error = UNSUPPORTED_OP
