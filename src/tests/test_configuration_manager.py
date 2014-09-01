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
        """Test whether `Configmanager.read' gets called with the expected
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


class HandleWriteValue(unittest.TestCase):
    @mock.patch("rpisps.configuration_manager.RpispsContext")
    def setUp(self, mock_context):
        self.config = ConfigurationManager()


    def test_acceptable_operations(self):
        """The only operation that is allowed for 'RequestValue' messages is
        'read', every other should raise an MessageFormatError"""
        request = { "operation": None, "collection": None, "target": None }
        for o in OPERATIONS:
            if o not in ("create", "delete", "update"):
                request["operation"] = o
                with self.subTest("Testing operation: %s" % o):
                    with self.assertRaises(MessageFormatError):
                        self.config.handle_request_value(**request)


    def test_acceptable_collections(self):
        """Only a collection of `WRITE_COLLECTION` is acceptable for
        'create', 'update', 'delete' requests."""
        request = { "operation": "create", "collection": None, "target": None }
        invalid_collections = ["templates", "localisation", "foo", "hello",
                               "instances_"]
        for c in invalid_collections:
            request["collection"] = c
            with self.subTest(collection=c):
                with self.assertRaises(MessageFormatError):
                    self.config.handle_request_value(**request)


    @mock.patch.object(ConfigurationManager, "create")
    def test_create_call(self, create_mock):
        """Test whether `Configmanager.create' gets called with the expected
        arguments."""
        requests = [
            { "operation": "create",
              "target": {},
              "collection": "instances" }
        ]
        for r in requests:
            with self.subTest(request=r):
                self.config.handle_write_value(**r)
                create_mock.assert_called_with(r["target"],
                                               r["collection"])


    @mock.patch.object(ConfigurationManager, "update")
    def test_update_call(self, update_mock):
        """Test whether `Configmanager.update' gets called with the expected
        arguments."""
        requests = [
            { "operation": "update",
              "target": {},
              "collection": "instances" }
        ]
        for r in requests:
            with self.subTest(request=r):
                self.config.handle_write_value(**r)
                update_mock.assert_called_with(r["target"],
                                               r["collection"])


    @mock.patch.object(ConfigurationManager, "delete")
    def test_delete_call(self, delete_mock):
        """Test whether `Configmanager.delete' gets called with the expected
        arguments."""
        requests = [
            { "operation": "delete",
              "target": {},
              "collection": "instances" }
        ]
        for r in requests:
            with self.subTest(request=r):
                self.config.handle_write_value(**r)
                delete_mock.assert_called_with(r["target"],
                                               r["collection"])


class ExtractPayload(unittest.TestCase):
    @mock.patch("rpisps.configuration_manager.RpispsContext")
    def setUp(self, mock_context):
        self.config = ConfigurationManager()


    def test_missing_operation(self):
        """A Payload without a "operation" key raises a MessageFormatError."""
        request = {
            "payload": {
                "target": {},
                "collection": "instances"
            }
        }
        with self.assertRaises(MessageFormatError):
            self.config.extract_payload(request)


    def test_missing_target(self):
        """A Payload without a "target" key raises a MessageFormatError."""
        request = {
            "payload": {
                "operation": "read",
                "collection": "instances"
            }
        }
        with self.assertRaises(MessageFormatError):
            self.config.extract_payload(request)


    def test_missing_collection(self):
        """A Payload without a "collection" key raises a MessageFormatError."""
        request = {
            "payload": {
                "operation": "read",
                "target": {},
            }
        }
        with self.assertRaises(MessageFormatError):
            self.config.extract_payload(request)


    def test_return_value(self):
        """'ConfigurationManager.extract_payload returns a tuple with the
        elements (operation, target, collection)."""
        request = {
            "payload": {
                "operation": "read",
                "target": {},
                "collection": "instances"
            }
        }
        result = self.config.extract_payload(request)
        payload = request["payload"]
        expected = (payload["operation"], payload["target"],
                    payload["collection"])
        self.assertEqual(result, expected)


class HandleRequest(unittest.TestCase):
    VALID_REQUEST_VALUE = [
        {
            "type": "RequestValue",
            "from": "somewhere",
            "payload": {
                "operation": "read",
                "target": {},
                "collection": "instances"
            }
        }
    ]
    VALID_WRITE_VALUE = [
        {
            "type": "WriteValue",
            "from": "somewhere",
            "payload": {
                "operation": "create",
                "target": {},
                "collection": "instances"
            }
        }
    ]
    VALID_REQUESTS = VALID_REQUEST_VALUE + VALID_WRITE_VALUE


    @mock.patch("rpisps.configuration_manager.RpispsContext")
    def setUp(self, mock_context):
        self.config = ConfigurationManager()


    @mock.patch.object(ConfigurationManager, "handle_request_value")
    def test_handle_request_value_call(self, mock):
        """Requests of type 'RequestValue' call handle_request_value with the
        correct arguments"""
        for r in self.VALID_REQUEST_VALUE:
            operation = r["payload"]["operation"]
            target = r["payload"]["target"]
            collection = r["payload"]["collection"]
            self.config.handle_request(r)
            mock.assert_called_once_with(operation, target, collection)


    @mock.patch.object(ConfigurationManager, "handle_write_value")
    def test_handle_write_value_call(self, mock):
        """Requests of type 'WriteValue' call handle_write_value with the
        correct arguments"""
        for r in self.VALID_WRITE_VALUE:
            operation = r["payload"]["operation"]
            target = r["payload"]["target"]
            collection = r["payload"]["collection"]
            self.config.handle_request(r)
            mock.assert_called_once_with(operation, target, collection)


if __name__ == '__main__':
    unittest.main()
