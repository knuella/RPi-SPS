from rpisps.rpispscontext import RpispsContext
from rpisps.constants import *


dummy_config = {}


class ConfigDummy():
    def __init__(self):
        self.context = RpispsContext()
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


    def reply_error(self, request):
        self.context.send_reply(request["dst"], status=1)


    def handle_request(self):
        request = self.context.recv_request()

        if "RequestValue" == request["type"]:
            handle_request_value(request)
        elif "WriteValue" == request["type"]:
            handle_write_value(request)
        else:
            reply_error(request)



def main():
    config = ConfigDummy()

    while True:
        config.handle_request()


if __name__ == '__main__':
    main()
