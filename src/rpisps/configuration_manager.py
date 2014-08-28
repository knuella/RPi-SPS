from rpisps.context import Context as RpispsContext
from rpisps.constants import *
from rpisps.message import MessageDecoder, MessageEncoder


READ_COLLECTIONS = ("templates", "instances", "localizations")
WRITE_COLLECTIONS = ("instances")


class ConfigurationManager():
    def __init__(self, decoder=None, encoder=None):
        if decoder is None:
            decoder = MessageDecoder()
        if encoder is None:
            encoder = MessageEncoder()

        self.context = RpispsContext(decoder, encoder)
        self.context.make_source_known()

        self.config_ready()


    def config_ready(self):
        self.context.publish("READY")


    def extract_payload(self, request):
        try:
            operation = request['payload']['operation']
            target = request['payload']['target']
            collection = request['payload']['collection']
        except KeyError:
            raise MessageFormatError()
        return (operation, target, collection)


    def handle_request_value(self, request):
        operation, target, collection = self.extract_payload(request)

        if operation != "read":
            raise MessageFormatError()
        if collection not in READ_COLLECTIONS:
            raise MessageFormatError()
        return self.read_config(target, collection)


    def handle_write_value(self, request):
        operation, target, collection = self.extract_payload(request)

        if collection not in WRITE_COLLECTIONS:
            raise MessageFormatError()
        if operation not in ("create", "update", "delete"):
            raise MessageFormatError()

        if "create" == operation:
            return self.create_config(target, collection)
        elif "update" == operation:
            return self.update_config(target, collection)
        elif "delete" == operation:
            return self.delete_config(target, collection)


    def reply_error(self, dst):
        self.context.send_reply(dst, status=1)


    def handle_request(self):
        request = self.context.recv_request()

        try:
            if "RequestValue" == request["type"]:
                result = self.handle_request_value(request)
            elif "WriteValue" == request["type"]:
                result = self.handle_write_value(request)
            else:
                raise MessageFormatError()
        except (MessageFormatError, DatabaseError) as e:
            self.context.reply_error(request["from"], e.message)
        else:
            self.context.send_reply(request["from"], result)


    def close(self):
        """Called when the ConfigurationManager is stopped

        either due to a KeyboardInterrupt or SIGTERM

        """
        pass


    def create_config(self, target, collection):
        """Add the target to the configuration collection

        'target' is a list of dictionaries holding new configurations
        to be added.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        the target should be added to.

        """
        raise NotImplementedError


    def read_config(self, target, collection):
        """Returns a list of dictionaries with configuration.

        'target' is a list of dictionaries holding identifiers for
        each of the requested configurations.  If the list is empty
        all elements from the specified 'collection' are retrieved.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        should be searched.

        """
        raise NotImplementedError


    def update_config(self, target, collection):
        """Replace the object with the same identifier as target with target.

        'target' is a list of dictionaries with each dictionary
        containing the new version of an object.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        the target should be replaced in.

        """
        raise NotImplementedError


    def delete_config(self, target, collection):
        """Delete the target from the configuration collection

        'target' is a list of dictionaries. Each dictionary containing
        the id of a configuration entry to be deleted.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        the target should be deleted from.

        """
        raise NotImplementedError
