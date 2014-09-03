import json
from file_dict import *

needed_meta = ('mtime', 'object_id')


class TemplateDict(FileDict):

    def get_file_data(self, filename):
        file_data = FileDict.get_file_data(self, filename)
        try:
            file_data['meta']['object_id'] = self[filename]['object_id']
        except KeyError:
            pass
        return file_data
    
    def get_file_content(self, import_file):
        import_filepath = pathjoin(self.import_path, import_file)
        json_file = open(import_filepath)
        try:
            content = json.load(json_file)
        except ValueError:
            raise ValueError('The template ' + import_filepath + \
                             ' is not readebal as json file.')
        return content
