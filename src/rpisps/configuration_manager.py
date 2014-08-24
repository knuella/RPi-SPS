from json import JSONDecoder, JSONEncoder

from rpisps.context import Context as RpispsContext
from rpisps.constants import *


dummy_config = {}


class ConfigurationManager():
    def __init__(self, json_decoder=JSONDecoder(), json_encoder=JSONEncoder()):
        self.context = RpispsContext(json_decoder, json_encoder)
        self.context.make_source_known()

        self.config_ready()


    def config_ready(self):
        self.context.publish("READY")


    def handle_request_value(self, request):
        try:
            reply = dummy_config[request["from"]]
            self.context.send_reply(request["from"], reply)
        except KeyError:
            self.reply_error(request["from"])


    def handle_write_value(self, request):
        self.reply_error(request)


    def reply_error(self, dst):
        self.context.send_reply(dst, status=1)


    def handle_request(self):
        request = self.context.recv_request()

        if "RequestValue" == request["type"]:
            self.handle_request_value(request)
        elif "WriteValue" == request["type"]:
            self.handle_write_value(request)
        else:
            self.reply_error(request)


    def close(self):
        """Called when the ConfigurationManager is stopped

        either due to a KeyboardInterrupt or SIGTERM

        """
        pass


    def create(self, target, collection):
        """Add the target to the configuration collection

        'target' is a dictionary holding new configurations
        to be added.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        the target should be added to.

        """
        raise NotImplementedError


    def read(self, targets, collection):
        """Returns a list of dictionaries with configuration.

        'targets' is a list of dictionaries holding identifiers
        (object_id) for each of the requested configurations.  If the
        list is empty all elements from the specified 'collection' are
        retrieved.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        should be searched.

        """
        raise NotImplementedError


    def update(self, target, collection):
        """Replace the object with the same id as target with target.

        'target' is the new version of object with targets id.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        the target should be replaced in.

        """
        raise NotImplementedError


    def delete(self, target, collection):
        """Delete the target from the configuration collection

        'target' is the id of configuration to be deleted.

        'collection' can be one of "templates", "instances",
        "localisation" and specifies which part of the configuration
        the target should be deleted from.

        """
        raise NotImplementedError





def main():
    config = ConfigurationManager()

    while True:
        config.handle_request()


if __name__ == '__main__':
    main()
