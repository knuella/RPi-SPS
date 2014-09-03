#!/usr/bin/python
from rpisps.context import Context as RpispsContext
from rpisps.constants import *
from rpisps.exceptions import *

from template_dict import *

templatepath = 'apps/templates'
cm = 'cm'

class TemplateManager():

    def __init__(self):
        self.context = RpispsContext()
        self.context.make_source_known()
        self.template_dict = TemplateDict(templatepath)
        self.load_template_list()

        self.equalize_not_listed()
        

    def load_template_list(self):
        rpl = self.context.request_value(cm, {'operation': 'read', 
                                              'target': {},
                                              'collection': 'templates'})
        if rpl['status'] != 0:
            raise RpispsException(rpl['payload']) 
        
        for item in rpl['payload']:
            file_data = item['file_data']
            file_data['meta']['object_id'] = item['object_id']
            
            self.template_dict[file_data['file_name']] = file_data['meta']


    def run(self):
        self.templates_ready()
        while True:
            r = self.context.recv_request()
            self.handle_request(r)
            

    def templates_ready(self):
        self.context.publish("READY")


    def handle_request(self, request):
        try:
            operation, target = self.extract_payload(request)
            if "RequestValue" == request["type"]:
                result = self.handle_request_value(operation, target)
            elif "WriteValue" == request["type"]:
                result = self.handle_write_value(operation, target)
            else:
                raise MessageFormatError()
        except (MessageFormatError) as e:
            self.reply_error(request["from"], e.message)
        else:
            self.context.send_reply(request["from"], result)

 
    def extract_payload(self, request):
        try:
            operation = request['payload']['operation']
            target = request['payload']['target']
        except KeyError:
            raise MessageFormatError()
        return (operation, target)


    def handle_request_value(self, operation, target):
        if operation != "read":
            raise MessageFormatError("operaton in wrong")
        if target not in ("not_listed", "modified", "deleted"):
            raise MessageFormatError("target is wrong")
        
        if "read" == operation:
            if "not_listed" == target:
                return self.template_dict.get_not_listed()
            elif "modified" == target:
                return self.template_dict.get_modified()
            elif "deleted" == target:
                return self.template_dict.get_deleted()


    def handle_write_value(self, operation, target):
        if operation != "equalize":
            raise MessageFormatError("operaton in wrong")
        if target not in ("not_listed", "modified", "deleted"):
            raise MessageFormatError("target is wrong")
        
        if "equalize" == operation:
            if "not_listed" == target:
                return self.equalize_not_listed()
            elif "modified" == target:
                return self.equalize_modified()
            elif "deleted" == target:
                return self.equalize_deleted()


    def reply_error(self, dst, errormessage=None):
        self.context.send_reply(dst, errormessage, status=1)

    
    def equalize_not_listed(self):
        not_listed = self.template_dict.get_not_listed()
        for item in not_listed:
            file_data = item['file_data']
            
            rpl = self.context.write_value(cm, {'operation': 'create', 
                                                 'target': [item],
                                                 'collection': 'templates'})
            if rpl['status'] != 0:
                raise RpispsException(rpl['payload']) 
            file_data['meta']['object_id'] = rpl['payload']
            
            self.template_dict[file_data['file_name']] = file_data['meta']
        return 'equalize not-listed-files with DB'

    
    def equalize_modified(self):
        modified = self.template_dict.get_modified()
        for item in modified:
            file_data = item['file_data']
            
            item['object_id'] = item['file_data']['object_id']
            del item['file_data']['object_id']
            rpl = self.context.write_value(cm, {'operation': 'update', 
                                                'targets': item,
                                                'collection': 'templates'})
            if rpl['status'] != 0:
                raise RpispsException(rpl['payload']) 
            
            self.template_dict[file_data['file_name']] = file_data['meta']
        return 'equalize modified-files with DB'


    def equalize_deleted(self):
        deleted = self.template_dict.get_deleted()
        for item in modified:
            file_data = item['file_data']

            self.context.write_value(cm, {'operation': 'delete', 
                                          'targets': item['object_id'],
                                          'collection': 'templates'})
            if rpl['status'] != 0:
                raise RpispsException(rpl['payload']) 

            del self.template_dict[file_data['file_name']]
        return 'equalize deleted-files with DB'



def main():
    config = TemplateManager()

    while True:
        config.run()


if __name__ == '__main__':
    main()

