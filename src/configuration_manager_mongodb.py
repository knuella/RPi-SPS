#!/usr/bin/python

import pymongo
from pymongo import MongoClient
from pymongo.cursor import Cursor
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
        """
        In every json object rename the key "object_id" to "_id" and
        convert it to an 'ObjectId'
        """
        try:
            o["_id"] = ObjectId(o["object_id"])
            del o["object_id"]
        except KeyError:
            pass
        except InvalidId:
            raise MessageFormatError('"object_id" is not a valid id'
                                     , o) from None
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
        """
        Replace ever "_id" key with "object_id" in the payload of a message
        """
        try:
            for part in o["payload"]:
                if "object_id" in part:
                    raise DatabaseError(
                        'There should not be an "object_id" field in a message',
                        o)
                if "_id" in part:
                    part["object_id"] = part["_id"]
                    del part["_id"]
        except (TypeError, KeyError):
            pass


class ConfigurationManagerMongoDB(ConfigurationManager):
    def __init__(self, config_db="opensps_config"):
        super().__init__(MessageDecoderMongoDB(), MessageEncoderMongoDB())

        self._db_client = MongoClient()
        self._db = self._db_client[config_db]


    def create(self, targets, collection):
        #self.sanity_check_modifying(targets, need_id=False)

        try:
            object_id = self._db[collection].insert(targets)
        except PyMongoError:
            # TODO: be more specific
            raise DatabaseError("Error creating new document", targets)
        return [object_id]


    def read(self, targets, collection):
        object_ids = []
        for t in targets:
            try:
                object_ids.append(t["_id"])
            except KeyError:
                raise MessageFormatError('Missing required id key', t)

        if object_ids:
            query = { "_id" : { "$in" : object_ids } }
        else:
            # get the whole collection if targets is empty
            query = {}

        try:
            result = self._db[collection].find(query)
        except PyMongoError:
            raise DatabaseError('Error retrieving from the Database')

        return list(result)


    def delete(self, targets, collection):
        self.sanity_check_modifying(targets, need_id=True)

        try:
            self._db[collection].remove(targets[0])
        except PyMongoError:
            raise DatabaseError('Error deleting object', targets[0])


    def update(self, targets, collection):
        #self.sanity_check_modifying(targets, need_id=True)

        try:
            result = self._db[collection].update(targets[0], targets[1])
        except PyMongoError:
            raise DatabaseError('Error updating object', targets[0])

        if result["n"] == 0:
            raise DatabaseError('Object to update did not exist', targets)
        elif result["n"] > 1:
            raise DatabaseError('Deleted more than one entry', targets)
        
        return list(result)


    def sanity_check_modifying(self, targets, need_id=False):
        """
        Raise a UnsupportedOperation exception if 'targets' contains more than
        one element.

        If 'need_id' is True raises a MessageFormatError if the key "_id" is
        not in the first target.
        """
        # necessary, because mongo has no built-in support for
        # transaction commits
        if len(targets) != 1:
            raise UnsupportedOperation('Can only modify one entry at a time', targets)
        if need_id and "_id" not in targets[0]:
            raise MessageFormatError('Missing required id key', targets[0])


    def raw_read(self, raw_request, collection):
        """
        Return a list of dictionaries with configuration.

        Args:
            raw_request: A dictionary that is passed unpacked to
                pymongo.collection.find.  Read the pymongo documentation for
                the parameters.
            collection (str): Specifies which part of the configuration
                the dictionaries in target refer to. Only "templates",
                "instances" or "localisation" are allowed.

        Returns:
            The list of dictionaries holding the matching targets.

        Raises:
            DatabaseError: Raised when the operation could not be completed.
        """
        try:
            result = self._db[collection].find(raw_request)
        except PyMongoError:
            raise DatabaseError('Error retrieving from Database') from None

        return list(result)


    def raw_delete(self, raw_request, collection):
        """
        Delete entries from the configuration collection

        Args:
            raw_requeset: A dictionary that is passed unpacked to
                pymongo.collection.remove.  Read the pymongo documentation for
                the parameters.
            collection (str): Specifies which part of the configuration
                the target should be deleted from (only "instances" is allowed).

        Raises:
            DatabaseError: Raised when the operation could not be completed.
        """
        try:
            self._db[collection].remove(raw_request)
        except PyMongoError:
            raise DatabaseError('Error deleting object') from None


if __name__ == '__main__':
    config = ConfigurationManagerMongoDB()
    config.run()
