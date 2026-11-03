"""Real localhost HTTP authorization tests for the VPS gate; no external network access."""
import http.client
import importlib.util
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/setup-vps/scripts/gate.py"
spec = importlib.util.spec_from_file_location("vps_gate_under_test", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        gate.DATA = cls.tmp.name
        Path(cls.tmp.name, "secret").write_bytes(os.urandom(32))
        Path(cls.tmp.name, "users").write_text("admin@example.test admin\nmember@example.test member\n")
        Path(cls.tmp.name, "ips").write_text("192.0.2.10/32\n")
        Path(cls.tmp.name, "lumail").write_text("key=test-only-no-network\nfrom=test@example.test\n")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), gate.Gate)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def request(self, method="GET", url="/.gate/verify", ip="192.0.2.10", cookie=None, body=None, extra=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        headers = {"X-Gate-IP": ip, "X-Forwarded-Method": method}
        if cookie is not None:
            headers["Cookie"] = "vps_gate=" + cookie
        if extra:
            headers.update(extra)
        try:
            conn.request("POST" if body is not None else "GET", url, body=body, headers=headers)
            response = conn.getresponse()
            result = response.status, dict(response.getheaders())
            response.read()
            return result
        finally:
            conn.close()

    def test_saved_ip_can_read_only(self):
        for method in ("GET", "HEAD"):
            status, headers = self.request(method=method)
            self.assertEqual(status, 204)
            self.assertEqual(headers.get("X-Gate-Role"), "user")
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            status, _ = self.request(method=method)
            self.assertEqual(status, 401)

    def test_saved_ip_cannot_access_admin_without_session(self):
        status, _ = self.request(url="/.gate/verify?need=admin")
        self.assertEqual(status, 302)

    def test_unlisted_ip_denied(self):
        status, _ = self.request(ip="192.0.2.99", method="POST")
        self.assertEqual(status, 401)

    def test_admin_session_and_member_roles(self):
        for email, role in (("admin@example.test", "admin"), ("member@example.test", "member")):
            token = gate.make_session(email)
            status, headers = self.request(method="POST", cookie=token, ip="192.0.2.99")
            self.assertEqual(status, 204)
            self.assertEqual(headers.get("X-Gate-Role"), role)
            status, headers = self.request(url="/.gate/verify?need=admin", cookie=token)
            self.assertEqual(status, 204 if role == "admin" else 403)

    def test_invalid_session_fails_closed(self):
        status, _ = self.request(method="POST", cookie="forged.session.token")
        self.assertEqual(status, 401)

    def test_saved_ip_can_reach_login(self):
        status, _ = self.request(url="/.gate/login")
        self.assertEqual(status, 200)

    def test_malformed_post_rejected(self):
        for length, body in (("garbage", b"a=1"), ("5000", b""), ("3", b"\xff\xfe\xff")):
            status, _ = self.request(url="/.gate/login", body=body, extra={"Content-Length": length})
            self.assertEqual(status, 400)

    def test_missing_proxy_ip_denied(self):
        status, _ = self.request(ip="", method="GET")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
