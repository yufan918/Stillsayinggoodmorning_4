import unittest
import requests
import subprocess
import time
import os
import sys

# Prefer plain text; no JSON Accept header so server can return text/plain
HEADERS_PLAIN_TEXT = {"Accept": "text/plain"}


class FlaskAppTests(unittest.TestCase):
    FLASK_PORT = 5000
    FLASK_URL = f"http://127.0.0.1:{FLASK_PORT}"
    process = None

    @classmethod
    def setUpClass(cls):
        app_path = os.path.join(os.path.dirname(__file__), 'app.py')
        if not os.path.exists(app_path):
            print(f"Error: app.py not found at {app_path}", file=sys.stderr)
            sys.exit(1)
        print(f"Starting Flask app from {app_path} on {cls.FLASK_URL}...")
        cls.process = subprocess.Popen([sys.executable, app_path], env=os.environ.copy())
        cls.wait_for_server()
        print("Flask app started.")

    @classmethod
    def tearDownClass(cls):
        if cls.process:
            print("Stopping Flask app...")
            cls.process.terminate()
            cls.process.wait()
            print("Flask app stopped.")

    @classmethod
    def wait_for_server(cls, timeout=60, interval=0.5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{cls.FLASK_URL}/health", headers=HEADERS_PLAIN_TEXT)
                if response.status_code == 200 and response.text.strip() == "OK":
                    print("Health check successful.")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(interval)
        raise TimeoutError("Flask app did not start within the given timeout.")

    def _debug_response(self, label, response):
        """Print full response (status and body) for debugging when something goes wrong."""
        print(f"[DEBUG] {label}: status_code={response.status_code}", file=sys.stderr)
        print(f"[DEBUG] {label}: response.text={repr(response.text)}", file=sys.stderr)
        print(f"[DEBUG] {label}: Content-Type={response.headers.get('Content-Type', 'not set')}", file=sys.stderr)

    def _assert_plain_text_ok(self, response, expected_text, endpoint_label):
        """Assert status 200 and that response content equals or contains expected text; print full response on failure."""
        if response.status_code != 200:
            self._debug_response(endpoint_label, response)
            self.assertEqual(response.status_code, 200, f"{endpoint_label}: expected 200, got {response.status_code}")
        text = response.text if isinstance(response.text, str) else response.text.decode("utf-8", errors="replace")
        if expected_text not in text:
            self._debug_response(endpoint_label, response)
            self.assertIn(expected_text, text, f"{endpoint_label}: expected substring {expected_text!r} in response body")

    def test_root_page(self):
        url = f"{self.FLASK_URL}/"
        print(f"Testing GET {url}")
        response = requests.get(url, headers=HEADERS_PLAIN_TEXT)
        self._assert_plain_text_ok(response, "Hello, World!", "GET /")

    def test_api_page(self):
        url = f"{self.FLASK_URL}/api"
        print(f"Testing GET {url}")
        response = requests.get(url, headers=HEADERS_PLAIN_TEXT)
        self._assert_plain_text_ok(response, "Welcome to the API!", "GET /api")

    def test_health_returns_ok(self):
        url = f"{self.FLASK_URL}/health"
        print(f"Testing GET {url}")
        response = requests.get(url, headers=HEADERS_PLAIN_TEXT)
        if response.status_code != 200 or "OK" not in response.text:
            self._debug_response("GET /health", response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("OK", response.text)


if __name__ == '__main__':
    unittest.main()
