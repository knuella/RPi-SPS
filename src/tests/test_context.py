import unittest
import unittest.mock as mock

from rpisps.context import Context

# used as the return value for the mock of Context._get_config which
# normally returns an argparse.Namespace with the attributes defined
# in the dictionary
retval_get_config = mock.Mock(**{
    "name": "test",
    "service_address": "tcp://127.0.0.10:6666",
    "request_address": "tcp://127.0.0.10:6665",
    "new_values_address": "tcp://127.0.0.10:5555",
    "submit_values_address": "tcp://127.0.0.10:555"
})

class BasicTests(unittest.TestCase):
    @mock.patch.object(Context, "_get_config", return_value=retval_get_config)
    def setUp(self, context_mock):
        self.ctx = Context()


    def test_reply_error_calls_send_reply(self):
        """send_reply is called from reply_error"""
        with mock.patch.object(self.ctx, "send_reply") as reply_mock:
            self.ctx.reply_error("somewhere", "errormessage")
            reply_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
