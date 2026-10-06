import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Add root folder to sys.path so database module is accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database


class handler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            data = database.get_all_data()
            self.send_json(data)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(size) if size > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
            database.save_all_data(payload)
            self.send_json({"success": True, "message": "Datele au fost salvate."})
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)
