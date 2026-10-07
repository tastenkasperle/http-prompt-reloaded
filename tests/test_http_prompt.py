"""
Hermetic Unit & Integration Tests for HTTP Prompt Reloaded.
Includes Fire Team Elite Security Hardening (SSRF, URL Traversal, Header Injection).
"""

import unittest
import http.server
import threading
import json
from src.core.engine import SessionContext, RequestExecutor, SecurityError
from src.mcp.server import HTTPPromptMCPServer


class MockHTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {
            "path": self.path,
            "headers": dict(self.headers),
            "message": "success"
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"received": body, "path": self.path}).encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Quiet logs


class TestHTTPPromptReloaded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ephemeral local test server on port 0
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), MockHTTPHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_cd_navigation(self):
        sess = SessionContext("http://api.local")
        self.assertEqual(sess.cd("/v1"), "http://api.local/v1")
        self.assertEqual(sess.cd("users"), "http://api.local/v1/users")
        self.assertEqual(sess.cd("42"), "http://api.local/v1/users/42")
        self.assertEqual(sess.cd(".."), "http://api.local/v1/users")
        self.assertEqual(sess.cd("/"), "http://api.local/")

    def test_request_execution_with_mock_server(self):
        sess = SessionContext(f"http://127.0.0.1:{self.port}")
        sess.cd("/api/status")
        sess.set_header("Authorization", "Bearer secret123")
        sess.set_param("sort", "desc")

        res = RequestExecutor.execute(sess, method="GET")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body)
        self.assertEqual(data["path"], "/api/status?sort=desc")
        self.assertEqual(data["headers"].get("Authorization"), "Bearer secret123")

    def test_post_execution(self):
        sess = SessionContext(f"http://127.0.0.1:{self.port}")
        sess.cd("/items")
        payload = {"name": "Laptop", "price": 999}
        res = RequestExecutor.execute(sess, method="POST", override_body=payload)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.body)
        self.assertIn("Laptop", data["received"])

    def test_mcp_server_protocol(self):
        server = HTTPPromptMCPServer()
        # 1. tools/list
        list_resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tools = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertIn("http_prompt_init", tools)
        self.assertIn("http_prompt_cd", tools)
        self.assertIn("http_prompt_execute", tools)

        # 2. init
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "http_prompt_init", "arguments": {"base_url": f"http://127.0.0.1:{self.port}"}}
        })

        # 3. cd & execute
        server.handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "http_prompt_cd", "arguments": {"path": "/mcp-test"}}
        })

        exec_resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "http_prompt_execute", "arguments": {"method": "GET"}}
        })
        content = json.loads(exec_resp["result"]["content"][0]["text"])
        self.assertEqual(content["status"], 200)
        self.assertIn("/mcp-test", content["url"])

    def test_security_crlf_header_injection(self):
        sess = SessionContext("http://api.local")
        with self.assertRaises(SecurityError):
            sess.set_header("X-Injected\r\nSet-Cookie: evil=1", "val")
        with self.assertRaises(SecurityError):
            sess.set_header("Authorization", "Bearer 123\nInjected-Header: evil")

    def test_security_ssrf_cloud_metadata_blocked(self):
        with self.assertRaises(SecurityError):
            SessionContext("http://169.254.169.254/latest/meta-data/")
        with self.assertRaises(SecurityError):
            SessionContext("http://metadata.google.internal/computeMetadata/v1/")

    def test_security_dangerous_schemes_blocked(self):
        with self.assertRaises(SecurityError):
            SessionContext("file:///etc/passwd")
        with self.assertRaises(SecurityError):
            SessionContext("gopher://127.0.0.1:25")

    def test_security_url_traversal_sanitization(self):
        sess = SessionContext("http://api.local")
        sess.cd("/api/v1/users/../../admin")
        self.assertEqual(sess.current_path, "/api/admin")
        # Relative traversal up one level
        sess.cd("%2e%2e/billing")
        self.assertEqual(sess.current_path, "/api/billing")
        # Traversal beyond root collapses safely to root
        sess.cd("../../../../../system")
        self.assertEqual(sess.current_path, "/system")


if __name__ == "__main__":
    unittest.main()
