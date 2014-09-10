import sys
import time

from rpisps.context import Context as RpispsContext
from rpisps.constants import *
from rpisps.message import MessageDecoder, MessageEncoder
from rpisps.exceptions import *

from exclusive_writebal import *


class InputDP:
    """ 
    This is a Controleprogramm to read something outside of the computer and
    connect to it over the sockets.

    To read from the sockets, send a RequestValue with the following payload:
    'operation': should be one of 
            'read_value', 'read_state' or 'read_all'
            without params
    
    For Example:
    {
        'payload': 
            {
                'operation': 'read_value', 
            }, 
        'from': 'test_context', 
        'dst': 'input', 
        'type': 'RequestValue'
    }


    Attributes:
        actual_value: 
            The value, which was read from the hardware.
        state (string): 
            The state of the connection to outside.
    """
    
    def __init__(self):

        self.context = RpispsContext()
        self.context.make_source_known()

        self._state = "don't know"
        self.read_outside_value()


    def run(self):
        self.ready()
        while True:
            r = self.context.recv_request()
            self.handle_request(r)


    def ready(self):
        self.context.publish("READY")


    def close(self):
        """Called when the ConfigurationManager is stopped
        either due to a KeyboardInterrupt or SIGTERM
        """
        pass


    def reply_error(self, dst, errormessage="unknown error"):
        self.context.send_reply(dst, errormessage, status=1)


    def handle_request(self, request):
        try:
            operation, params = self.extract_payload(request)

            if "RequestValue" == request["type"]:
                result = self.handle_request_value(operation, params)
            elif "WriteValue" == request["type"]:
                params['req_programm'] = request['from']
                result = self.handle_write_value(operation, params)
            else:
                raise MessageFormatError()
        except (MessageFormatError, ExclusiveBlockError) as e:
            self.reply_error(request["from"], e.message)
        else:
            self.context.send_reply(request["from"], result)


    def extract_payload(self, request):
        try:
            operation = request['payload']['operation']
        except KeyError:
            raise MessageFormatError()
        try:
            params = request['payload']['params']
        except KeyError:
            params = {}
        return (operation, params)


    def handle_request_value(self, operation, params):
        try:
            if "read_value" == operation:
                return self.read_value()
            elif "read_state" == operation:
                return self._state
            elif "read_all" == operation:
                return self.return_all()
            else:
                message = "unsupportet operation"
                raise MessageFormatError(message)
        except TypeError as e:
            raise MessageFormatError(e.args[0])


    def read_value(self):
        self.read_outside_value()
        return self._actual_value


    def return_all(self):
        return {'value': self.read_value(),
                'state': self._state,
               }


    def publish_value(self):
        self.context.publish(self.return_all)


    def read_outside_value(self):    
        """ Sets "state" to "Hardware Error", if value can't be read.
        """
        self._state = "good"
        self._actual_value = 5
        #raise NotImplementedError() 




def main():
    dp = InputDP()
    dp.run()


if __name__ == '__main__':
    main()
