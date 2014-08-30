#!/usr/bin/python

import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

from rpisps.configuration_manager import ConfigurationManager
from rpisps.exceptions import *
from rpisps.message import MessageDecoder, MessageEncoder



class MessageDecoderMongoDB(MessageDecoder):
    def __init__(self):
        super().__init__(object_hook=self.hook)


    @staticmethod
    def hook(o):
        try:
            o["_id"] = o["object_id"]
            del o["object_id"]
        except KeyError:
            pass
        return o


class MessageEncoderMongoDB(MessageEncoder):
    def encode(self, o):
        self.replace_id(o)
        return super().encode(o)


    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        super().default(o)


    def replace_id(self, o):
        try:
            for e in o["payload"]:
                if "_id" in e:
                    # TODO: raise everything crashing exception
                    pass
                if "object_id" in e:
                    e["_id"] = e["object_id"]
                    del e["object_id"]
        except (TypeError, KeyError):
            pass


class ConfigurationManagerMongoDB(ConfigurationManager):
    def __init__(self, config_db="opensps_config"):
        super().__init__(MessageDecoderMongoDB(), MessageEncoderMongoDB())

        self._db_client = MongoClient()
        self._db = self._db_client[config_db]


    def create(self, targets, collection):
        self.sanity_check_modifying(targets, need_id=False)

        try:
            object_id = self._db[collection].insert(targets[0])
        except PyMongoError:
            raise DatabaseError()
        return [object_id]


    def read(self, targets, collection):
        object_ids = []
        for t in targets:
            try:
                object_ids.append(t["_id"])
            except KeyError:
                raise MessageFormatError()

        if object_ids:
            query = { "_id" : { "$in" : object_ids } }
        else:
            # get the whole collection if targets is empty
            query = {}

        try:
            result = self._db[collection].find(query)
        except PyMongoError:
            raise DatabaseError()

        return result


    def delete(self, targets, collection):
        self.sanity_check_modifying(targets, need_id=True)

        try:
            self._db[collection].remove(targets[0])
        except PyMongoError:
            raise DatabaseError()


    def update(self, targets, collection):
        self.sanity_check_modifying(targets, need_id=True)

        try:
            result = self._db[collection].update(targets[0], multi=False)
        except PyMongoError:
            raise DatabaseError()

        if result["n"] == 0:
            raise DatabaseError()
        elif result["n"] > 1:
            raise DatabaseError()


    def sanity_check_modifying(self, targets, need_id=False):
        if len(targets) != 1:
            raise UnsupportedOperation()
        if need_id and "_id" not in targets[0]:
            raise MessageFormatError()


if __name__ == '__main__':
    config = ConfigurationManagerMongoDB()
    config.run()
