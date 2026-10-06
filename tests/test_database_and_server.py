"""Test suite to verify SQLite database operations and server API endpoints."""
import os
import sys
import unittest
import json
import threading
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import server

class TestDentaDatabase(unittest.TestCase):
    def setUp(self):
        # Ensure fresh db initialization
        database.init_db()

    def test_database_get_all_data(self):
        data = database.get_all_data()
        self.assertIn("clinic", data)
        self.assertIn("patients", data)
        self.assertIn("appointments", data)
        self.assertIn("doctors", data)
        self.assertIn("records", data)
        self.assertTrue(len(data["patients"]) >= 3)
        self.assertEqual(data["clinic"]["name"], "Denta Atelier Centrală")

    def test_database_save_and_retrieve(self):
        data = database.get_all_data()
        test_patient_id = "test_patient_123"
        data["patients"].append({
            "id": test_patient_id,
            "first": "Ion",
            "last": "Creangă",
            "phone": "069 999 888",
            "sex": "M",
            "birth": 1980,
            "nid": "1234567890123",
            "owner": "u1",
            "status": "open",
            "shared": False
        })
        database.save_all_data(data)

        # Retrieve again
        updated = database.get_all_data()
        ids = [p["id"] for p in updated["patients"]]
        self.assertIn(test_patient_id, ids)

        # Clean up by resetting to seed
        database.reset_to_seed()
        reset_data = database.get_all_data()
        reset_ids = [p["id"] for p in reset_data["patients"]]
        self.assertNotIn(test_patient_id, reset_ids)
        self.assertEqual(len(reset_data["patients"]), 3)


class TestDentaServerEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()
        # Bind server to random available port
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_get_api_status(self):
        url = f"http://127.0.0.1:{self.port}/api/status"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "online")
            self.assertEqual(data["database_type"], "sqlite")

    def test_get_api_data(self):
        url = f"http://127.0.0.1:{self.port}/api/data"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("clinic", data)
            self.assertIn("patients", data)
            self.assertEqual(data["clinic"]["name"], "Denta Atelier Centrală")

    def test_post_api_data_save(self):
        url = f"http://127.0.0.1:{self.port}/api/data"
        data = database.get_all_data()
        data["clinic"]["phone"] = "+373 22 999 000"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res["success"])

        # Check that it persisted
        updated = database.get_all_data()
        self.assertEqual(updated["clinic"]["phone"], "+373 22 999 000")

        # Reset to seed
        database.reset_to_seed()

if __name__ == "__main__":
    unittest.main()
