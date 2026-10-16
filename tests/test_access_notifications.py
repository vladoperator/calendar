"""Registration webhook tests. No real accounts or email are created."""
import io
import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from access_notifications import handle_access_request


SECRET = "test-webhook-secret-with-at-least-32-characters"
USER_ID = "fdd2b742-8349-4bc3-8078-78d492543511"


class FakeHandler:
    def __init__(self, event, authorization=f"Bearer {SECRET}"):
        body = json.dumps(event).encode()
        self.headers = {"Authorization": authorization, "Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.result = None

    def send_json(self, payload, status=200):
        self.result = (status, payload)


class RegistrationNotificationTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "ACCESS_REQUEST_WEBHOOK_SECRET": SECRET,
            "RESEND_API_KEY": "test-api-key",
            "REGISTRATION_EMAIL_FROM": "Denta Atelier <requests@example.test>",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.event = {
            "type": "INSERT", "schema": "public", "table": "clinic_users",
            "record": {"id": USER_ID, "email": "new.user@example.test", "approved": False},
        }

    @patch("access_notifications.urllib.request.urlopen")
    def test_untrusted_browser_cannot_send_email(self, send):
        handler = FakeHandler(self.event, authorization="Bearer incorrect")
        handle_access_request(handler)
        self.assertEqual(handler.result[0], 401)
        send.assert_not_called()

    @patch("access_notifications.urllib.request.urlopen")
    def test_notification_has_fixed_recipient_and_no_credentials(self, send):
        send.return_value.__enter__.return_value = io.BytesIO(b'{"id":"email-123"}')
        self.event["record"].update({"password": "never-send-this", "to": "other@example.test"})
        handler = FakeHandler(self.event)
        handle_access_request(handler)
        self.assertEqual(handler.result, (200, {"sent": True}))
        request = send.call_args.args[0]
        message = json.loads(request.data)
        self.assertEqual(message["to"], ["chathot000@gmail.com"])
        self.assertIn("new.user@example.test", message["text"])
        self.assertNotIn("never-send-this", message["text"])
        self.assertNotIn("test-api-key", message["text"])
        self.assertEqual(request.get_header("Idempotency-key"), f"clinic-access/{USER_ID}")

    @patch("access_notifications.urllib.request.urlopen")
    def test_approved_accounts_and_unrelated_events_do_not_notify(self, send):
        for field, value in [("type", "UPDATE"), ("table", "clinic_state"), ("schema", "auth")]:
            event = {**self.event, field: value}
            handler = FakeHandler(event)
            handle_access_request(handler)
            self.assertEqual(handler.result, (200, {"ignored": True}))
        self.event["record"]["approved"] = True
        handler = FakeHandler(self.event)
        handle_access_request(handler)
        self.assertEqual(handler.result, (200, {"ignored": True}))
        send.assert_not_called()

    @patch("access_notifications.urllib.request.urlopen")
    def test_malformed_payloads_do_not_send(self, send):
        for event in [[], {**self.event, "record": None},
                      {**self.event, "record": {**self.event["record"], "id": "invalid"}},
                      {**self.event, "record": {**self.event["record"], "email": "a@b.test\nBcc: x@y.test"}}]:
            handler = FakeHandler(event)
            handle_access_request(handler)
            self.assertEqual(handler.result[0], 400)
        handler = FakeHandler(self.event)
        handler.headers["Content-Length"] = "20000"
        handle_access_request(handler)
        self.assertEqual(handler.result[0], 413)
        send.assert_not_called()

    @patch("access_notifications.urllib.request.urlopen")
    def test_missing_delivery_configuration_is_visible(self, send):
        with patch.dict(os.environ, {"RESEND_API_KEY": ""}):
            handler = FakeHandler(self.event)
            handle_access_request(handler)
            self.assertEqual(handler.result[0], 503)
        with patch.dict(os.environ, {"ACCESS_REQUEST_WEBHOOK_SECRET": ""}):
            handler = FakeHandler(self.event)
            handle_access_request(handler)
            self.assertEqual(handler.result[0], 503)
        send.assert_not_called()

    @patch("access_notifications.urllib.request.urlopen", side_effect=urllib.error.URLError("offline"))
    def test_delivery_failure_can_be_detected_and_retried(self, send):
        handler = FakeHandler(self.event)
        handle_access_request(handler)
        self.assertEqual(handler.result[0], 502)
        self.assertNotIn("sent", handler.result[1])


if __name__ == "__main__":
    unittest.main()
