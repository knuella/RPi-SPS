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
        request = { "operation": None, "collection": None }
        for o in OPERATIONS:
            if o != "read":
                request["operation"] = o
                with self.subTest("Testing operation: %s" % o):
                    with self.assertRaises(MessageFormatError):
                        self.config.handle_request_value(request)


if __name__ == '__main__':
    unittest.main()
