from os.path import isdir, getmtime, join as pathjoin 
from os import listdir, walk as dirwalk
from collections import UserDict;

needed_meta = []
needed_meta.append('mtime')


class FileDict(UserDict):
    def __init__(self, import_path, *args, **kwargs):
        if isdir(import_path):
            self.import_path = import_path
        else:
            raise FileNotFoundError("Path doesn't exist")
        
        UserDict.__init__(self, *args, **kwargs)

    def __setitem__(self, filename, value):
        meta = {}
        try:
            for key in needed_meta:
                meta[key] = value[key]
        except KeyError:
            message = 'Value must be a instance of a dict with ' + \
                      needed_meta + '.'
            raise TypeError(message)
        UserDict.__setitem__(self, filename, meta)

    def is_modified_path(self):
        return getmtime(self.import_path) > self.get_last_loaded_mtime()

    def get_last_loaded_mtime(self):
        last = 0
        for listed_file, meta in self.items():
            if last < meta['mtime']:
                last = meta['mtime']
        return last

    def is_modified(self, listed_file):
        import_filepath = pathjoin(self.import_path, listed_file)
        return getmtime(import_filepath) > self[listed_file]['mtime']
    
    def get_modified(self):
        modified = []
        if self.is_modified_path():
            for listed_file, meta in self.items():
                try:
                    if self.is_modified(listed_file):
                        data = self.get_file_content(listed_file)
                        data['file_data'] = self.get_file_data(listed_file)
                        modified.append(data)
                except FileNotFoundError:
                    pass
        return modified

    def get_not_listed(self):
        not_listed = []
        if self.is_modified_path():
            root, dirs, import_files = next(dirwalk(self.import_path))
            for import_file in import_files:
                if import_file not in self:
                    data = self.get_file_content(import_file)
                    data['file_data'] = self.get_file_data(import_file)
                    not_listed.append(data)
        return not_listed

    def get_deleted(self):
        deleted = []
        if self.is_modified_path():
            root, dirs, import_files = next(dirwalk(self.import_path))
            for listed_file, mata in self.items():
                if listed_file not in import_files:
                    data = {}
                    data['file_data'] = self.get_file_data(listed_file)
                    deleted.append(data)
        return deleted

    def get_file_data(self, filename):
        import_filepath = pathjoin(self.import_path, filename)
        file_data = {'file_name':filename}
        file_data['meta'] = {}
        try:
            file_data['meta']['mtime'] = getmtime(import_filepath)
        except FileNotFoundError:
            file_data['meta']['mtime'] = ''
        return file_data

    def get_file_content(self, filename):
        """ Should return a dict with the content of the file or other file
        information.

        For example: 
        - return a dict, when the file is a json file
        - return the import path, when the file is a python script
        """
        return {}

