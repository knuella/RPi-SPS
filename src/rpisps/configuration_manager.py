from rpisps.context import Context as RpispsContext
from rpisps.constants import *
from rpisps.message import MessageDecoder, MessageEncoder
from rpisps.exceptions import *


READ_COLLECTIONS = ("templates", "instances", "localisation")
WRITE_COLLECTIONS = ("instances")


class ConfigurationManager():
    """
    ConfigurationManager is a base class for various configuration back-ends.

    Subclasses need to implement the methods create, read, update, delete.
    """
    def __init__(self, decoder=None, encoder=None):
        """
        Args:
            decoder: MessageDecoder instance passed to rpisps.context.Context
            encoder: MessageEncoder instance passed to rpisps.context.Context
        """
        if decoder is None:
            decoder = MessageDecoder()
        if encoder is None:
            encoder = MessageEncoder()

        self.context = RpispsContext(decoder, encoder)
        self.context.make_source_known()


    def run(self):
        self.config_ready()
        while True:
            r = self.context.recv_request()
            self.handle_request(r)


    def config_ready(self):
        """
        Inform services that the configuration manager is ready to service
        requests.

        This is intended to be used in conjunction with a launcher
        that starts all services and depends on the configuration
        manager to be running in order for it to get the information
        about the programs it is supposed to run.
        """
        self.context.publish("READY")


    def extract_payload(self, request):
        """
        Args:
            request: A JSON object representing a full request with a payload.

        Returns:
            A tuple (operating, target, collection)

        Raises:
            MessageFormatError: A required key in the request is missing.
        """
        try:
            operation = request['payload']['operation']
            target = request['payload']['target']
            collection = request['payload']['collection']
        except KeyError:
            raise MessageFormatError()
        return (operation, target, collection)


    def handle_request_value(self, operation, target, collection):
        """
        Called with RequestValue type messages

        Args:
            operation (str): The operation to perform (only "read" is allowed)
            target: A list of dictionaries.  Each dictionary specifing
                a target to act upon.
            collection (str): The name of the collection in which the targets
                are located.  Only collection names that are in READ_COLLECTIONS
                are acceptable.

        Returns:
            The result of the performed operation.

        Raises:
            MessageFormatError: When the operation is not "read" or
                the collection is not part of READ_COLLECTIONS.
        """
        if operation != "read":
            raise MessageFormatError()
        if collection not in READ_COLLECTIONS:
            raise MessageFormatError()
        return self.read(target, collection)


    def handle_write_value(self, operation, target, collection):
        """
        Called with RequestValue type messages

        Args:
            operation (str): The operation to perform
                (only "create", "update", "delete" are allowed)
            target: A list of dictionaries.  Each dictionary specifing
                a target to act upon.
            collection (str): The name of the collection in which the targets
                are located.  Only collection names that are in
                WRITE_COLLECTIONS are acceptable.

        Returns:
            The result of the performed operation.

        Raises:
            MessageFormatError:
                When the operation is not one of "create", "update", "delete" or
                the collection is not part of WRITE_COLLECTIONS.
        """
        if collection not in WRITE_COLLECTIONS:
            raise MessageFormatError()
        if operation not in ("create", "update", "delete"):
            raise MessageFormatError()

        if "create" == operation:
            return self.create(target, collection)
        elif "update" == operation:
            return self.update(target, collection)
        elif "delete" == operation:
            return self.delete(target, collection)


    def reply_error(self, dst):
        self.context.send_reply(dst, status=1)


    def handle_request(self, request):
        """
        Dispatches to handle_request_value or handle_write_value
        depending on the message type.

        The result of the call, or on an exception an error message, is
        send to the requester.
        """
        try:
            operation, target, collection = self.extract_payload(request)

            if "RequestValue" == request["type"]:
                result = self.handle_request_value(operation,
                                                   target, collection)
            elif "WriteValue" == request["type"]:
                result = self.handle_write_value(operation,
                                                 target, collection)
            else:
                raise MessageFormatError()
        except (MessageFormatError, DatabaseError) as e:
            self.context.reply_error(request["from"], e.message)
        else:
            self.context.send_reply(request["from"], result)


    def close(self):
        """
        Called when the ConfigurationManager is stopped

        either due to a KeyboardInterrupt or SIGTERM

        """
        # TODO:
        pass


    def create(self, target, collection):
        """
        Add the target to the configuration collection

        Args:
            target: is a list of dictionaries holding new configurations
                to be added.
            collection (str): Specifies which part of the configuration
                the target should be added to (only "instances" is allowed).

        Returns:
            A list of new object identifiers for the created targets

        Raises:
            DatabaseError: Raised when the operation could not be completed.
                No changes to the stored configuration should have occured.
            UnsupportedOperation: Raised when the back-end cannot handle more
                than one target at a time.
        """
        raise NotImplementedError


    def read(self, target, collection):
        """
        Return a list of dictionaries with configuration.

        Args:
            target: is a list of dictionaries holding identifiers for
                each of the requested configurations.  If the list is empty
                all elements from the specified 'collection' are retrieved.
            collection (str): Specifies which part of the configuration
                the dictionaries in target refer to. Only "templates",
                "instances" or "localisation" are allowed.

        Returns:
            The list of dictionaries holding the matching targets.

        Raises:
            DatabaseError: Raised when the operation could not be completed.
        """
        raise NotImplementedError


    def update(self, target, collection):
        """
        Replace the object with the same identifier as target with target.

        Args:
            target: is a list of dictionaries with each dictionary
                containing the new version of an object.  Each dictionary is
                required to contain an object identifier.
            collection (str): Specifies which part of the configuration
                the targets are in (only "instances" is allowed).

        Raises:
            DatabaseError: Raised when the operation could not be completed.
            UnsupportedOperation: Raised when the back-end cannot handle more
                than one target at a time.
        """
        raise NotImplementedError


    def delete(self, target, collection):
        """
        Delete the target from the configuration collection

        Args:
            target: is a list of dictionaries.  Each dictionary containing
                the id of a configuration entry to be deleted.
            collection (str): Specifies which part of the configuration
                the target should be deleted from (only "instances" is allowed).

        Raises:
            DatabaseError: Raised when the operation could not be completed.
            UnsupportedOperation: Raised when the back-end cannot handle more
                than one target at a time.
        """
        raise NotImplementedError


    # The raw_* variants of the normal CRUD methods are more a
    # work-around than an actual feature.  Cases that require the use
    # of these methods should be abstracted and put in the normal
    # methods.
    def raw_create(self, raw_request, collection):
        """
        The exact usage of 'raw_request' depends on the used backend.
        """
        raise UnsupportedOperation("The backend has not implemented raw_create")


    def raw_read(self, raw_request, collection):
        """
        The exact usage of 'raw_request' depends on the used backend.
        """
        raise UnsupportedOperation("The backend has not implemented raw_read")


    def raw_update(self, raw_request, collection):
        """
        The exact usage of 'raw_request' depends on the used backend.
        """
        raise UnsupportedOperation("The backend has not implemented raw_update")


    def raw_delete(self, raw_request, collection):
        """
        The exact usage of 'raw_request' depends on the used backend.
        """
        raise UnsupportedOperation("The backend has not implemented raw_delete")
