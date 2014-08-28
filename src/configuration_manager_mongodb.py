#!/usr/bin/python

import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

from configuration_manager import ConfigurationManager
from rpisps.exceptions import *


class ConfigurationManagerMongoDB(ConfigurationManager):
    def __init__(self, config_db="opensps_config"):
        super().__init__()

        self._db_client = MongoClient()
        self._db = self._db_client[config_db]


    def create(self, targets, collection):
        t = targets[0]
        try:
            object_id = self._db[collection].insert(t)
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
        try:
            self._db[collection].remove(targets[0])
        except PyMongoError:
            raise DatabaseError()


    def update(self, targets, collection):
        if len(targets) != 1:
            raise UnsupportedOperation()
        if "_id" not in targets[0]:
            raise MessageFormatError()

        try:
            result = self._db[collection].update(targets[0], multi=False)
        except PyMongoError:
            raise DatabaseError()

        if result["n"] == 0:
            raise DatabaseError()
        elif result["n"] > 1:
            raise DatabaseError()
