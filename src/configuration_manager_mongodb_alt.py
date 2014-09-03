#!/usr/bin/python
import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId
from rpisps.exceptions import *
from rpisps.configuration_manager import ConfigurationManager

class ConfigurationManagerMongoDB(ConfigurationManager):
    """Handle requests of reading and writing configfiles and stores all the
    files in a MongoDB. Loads configuration templates from plugins.
    """
    

    def __init__(self, config_db="opensps_config"):
        """Connect to the database and to the socket-communication.""" 
        super().__init__()
        self.connect_to_db(config_db)

    
    def connect_to_db(self, config_db):
        """Connect to the MongoDB 'config_db'"""
        self._db_client = pymongo.MongoClient()
        self._db = self._db_client[config_db]


    def read(self, find_dict, collection):
        """Implementation of the get_config method"""
        try:
            result_configs = self._db[collection].find(find_dict)    
        except TypeError as e:
            raise MessageFormatError('Target must be an instance of dict')
        except pymongo.errors.PyMongoError as e:
            raise DatabaseError(e.args)

        nopointer_configs = []
        for config in result_configs:
            config = self.mongo_2_json(config)
            nopointer_configs.append(config)
        return nopointer_configs


    def create(self, save_dict, collection):
        """Implementation of the save_config method"""
        save_dict = self.json_2_mongo(save_dict)
        try:
            object_id = str(self._db[collection].insert(save_dict))
            #TODO: exception wird nicht gefangen, warum???
        except pymongo.errors.PyMongoError as e:
            raise DatabaseError(e.args[0])
        return object_id


    def delete(self, object_id, collection):
        """Implementation of the delete_config method"""
        try:
            result = self._db[collection].remove({'_id':ObjectId(object_id)})
        except InvalidId as e:
            raise MessageFormatError(e.args[0])
        except pymongo.errors.PyMongoError as e:
            raise DatabaseError(e.args[0])
        if result['ok'] == 1 and result['n']:
            return True
        else:
            return False


    def mongo_2_json(self, document):
        """Converts a MongoDB-file to a json-file.
        Means replace key '_id' with 'object_id'.
        """
        document['object_id'] = str(document['_id'])
        del document['_id']
        return document


    def json_2_mongo(self, document):
        """Converts a json-file to a MongoDB-file.
        Means replace the key 'object_id' with '_id'.
        """
        if 'object_id' in document:
            try:
                document['_id'] = ObjectId(document['object_id'])
                del document['object_id']
            except InvalidId as e:
                raise MessageFormatError(e.args[0])
        return document



def main():
    config = ConfigurationManagerMongoDB()

    while True:
        config.run()


if __name__ == '__main__':
    main()
