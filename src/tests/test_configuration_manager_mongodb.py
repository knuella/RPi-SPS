import unittest

from bson.objectid import ObjectId

from configuration_manager_mongodb import MessageDecoderMongoDB
from configuration_manager_mongodb import MessageEncoderMongoDB


class MessageDecoder(unittest.TestCase):
    def setUp(self):
        self.test_dicts = [
            {
                "object_id": "5408bace9b89e72028926374",
                "some_key": "test"
            }
        ]

        self.decoder = MessageDecoderMongoDB()


    def test_hook_only_object_id(self):
        """The hook method only affects the "object_id" key"""
        for d in self.test_dicts:
            copy = d.copy()
            self.decoder.hook(d)
            del copy["object_id"]
            del d["_id"]
            self.assertEqual(d, copy)


    def test_hook_id_is_objectid(self):
        """The hook method makes an bson.ObjectId from the "object_id" key and
        stores it into "_id" """
        for d in self.test_dicts:
            copy = d.copy()
            self.decoder.hook(d)
            self.assertEqual(ObjectId(copy["object_id"]), d["_id"])


    def test_after_hook_no_more_object_id(self):
        """The hook method removes any "object_id" key."""
        for d in self.test_dicts:
            self.decoder.hook(d)
            self.assertNotIn("object_id", d)


if __name__ == '__main__':
    unittest.main()
