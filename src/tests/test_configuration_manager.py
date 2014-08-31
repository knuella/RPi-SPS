import unittest
import unittest.mock as mock

from rpisps.configuration_manager import ConfigurationManager
from rpisps.configuration_manager import READ_COLLECTIONS, WRITE_COLLECTIONS
from rpisps.exceptions import *

OPERATIONS = ("create", "read", "update", "delete")


class HandleRequestValue(unittest.TestCase):
    @mock.patch("rpisps.configuration_manager.RpispsContext")
    def setUp(self, mock_context):
        self.config = ConfigurationManager()


    def test_only_read_operation(self):
        """The only operation that is allowed for 'RequestValue' messages is
        'read', every other should raise an MessageFormatError"""
        request = { "operation": None, "collection": None, "target": None }
        for o in OPERATIONS:
            if o != "read":
                request["operation"] = o
                with self.subTest("Testing operation: %s" % o):
                    with self.assertRaises(MessageFormatError):
                        self.config.handle_request_value(**request)


    def test_acceptable_collection(self):
        """Only a collection of `READ_COLLECTION` is acceptable for 'read'
        requests."""
        request = { "operation": "read", "collection": None, "target": None }
        invalid_collections = ["foo", "hello", "instances_"]
        for c in invalid_collections:
            request["collection"] = c
            with self.subTest(collection=c):
                with self.assertRaises(MessageFormatError):
                    self.config.handle_request_value(**request)


    def test_read_call(self):
        """Test weather `Configmanager.read' gets called with the expected
        arguments."""
        requests = [
            { "operation": "read",
              "target": {},
              "collection": "instances" }
        ]
        for r in requests:
            with self.subTest(request=r):
                with mock.patch.object(ConfigurationManager, "read") \
                     as read_mock:
                    self.config.handle_request_value(**r)
                    read_mock.assert_called_with(r["target"],
                                                 r["collection"])


if __name__ == '__main__':
    unittest.main()
