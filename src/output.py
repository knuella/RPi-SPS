from rpisps.context import Context as RpispsContext
from rpisps.constants import *
from rpisps.message import MessageDecoder, MessageEncoder
from rpisps.exceptions import *

from exclusive_writebal import *


class OutputDP:
    """ 
    This is a Controleprogramm to change something outside of the computer and
    connect it over the sockets.

    To read from the sockets, send a RequestValue with the following payload:
    'operation': should be one of 
            'read_value', 'read_exclusive', 'read_state' or 'read_all'
            without params
    
    To write from the sockets, send a WriteValue with the following payload:
    'operation': should be one of 
            'write_value', with 'params': <your_value>,
            or 'write_exclusive', 'delete_exclusive' 
            without params
    
    For Example:
    {
        'payload': 
            {
                'operation': 'write_value', 
                'params': {'value': 1}
            }, 
        'from': 'test_context', 
        'dst': 'output', 
        'type': 'WriteValue'
    }


    Attributes:
        safety_value (boolean or float): 
            This value will be set, if there is no programm, which want to
            set an other one. This shoult bring no threat, when writed to
            the hardware.
        actual_value (ExclusiveWritebal): 
            The value, witch will be written to the hardware.
        state (string): 
            The state of the connection to outside.
    """
    
    def __init__(self, safety_value):

        self.context = RpispsContext()
        self.context.make_source_known()

        self._safety_value = safety_value
        self._actual_value = ExclusiveWritebal(safety_value)
        self._state = "don't know"


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
        self._actual_value = self._safety_value
        self.write_physical_value()


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
            if "read_exclusive" == operation:
                return self._actual_value.get_exclusive()
            elif "read_value" == operation:
                return self._actual_value.get_value()
            elif "read_state" == operation:
                return self._state
            elif "read_all" == operation:
                return self._return_all()
            else:
                message = "unsupportet operation"
                raise MessageFormatError(message)
        except TypeError as e:
            raise MessageFormatError(e.args[0])


    def return_all(self):
        return {'exclusive': self._actual_value.get_exclusive(),
                'value': self._actual_value.get_value(),
                'state': self._state,
               }


    def handle_write_value(self, operation, params):

        try:
            if "write_exclusive" == operation:
                return self.write_exclusive(**params)
            elif "delete_exclusive" == operation:
                return self.delete_exclusive(**params)
            elif "write_value" == operation:
                return self.write_value(**params)
            else:
                message = "unsupportet operation"
                raise MessageFormatError(message)
        except TypeError as e:
            raise MessageFormatError(e.args[0])


    def write_exclusive(self, req_programm):
        """ Set the exclusive flag to the programm.
        If this flag is set, the programm is the only one,
        which can use the set_value method.
        Args:
            programm (string): The name from the programm with exclusive
                               writing rights.
        """
        self._actual_value.set_exclusive(req_programm)
        return self.return_all()


    def delete_exclusive(self, req_programm):
        """ Set the exclusive flag of actaul_value to None.
        Args:
            programm (string): the name from the programm with exclusive
            writing rights.
        """
        self._actual_value.del_exclusive(req_programm)
        return self.return_all()

    
    def write_value(self, value, req_programm): 
        """ Writes to the hardware.
        Args:
            programmname (string): the programm, which want to set the value. 
            to_set_value (dynamic): value which will be write. Depands on the
                                    hardware-type.
        """
        self._actual_value.set_value(value, req_programm)
        self.write_outside_value()
        return self.return_all()


    def write_outside_value(self):    
        """ Sets "state" to "Hardware Error", if value can't be written.
        """
        print("actual_value = " + str(self._actual_value.get_value()))
        self._state = "good"
        #raise NotImplementedError() 




def main():
    dp = OutputDP(1)
    while True:
        dp.run()


if __name__ == '__main__':
    main()
